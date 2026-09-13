"""Image post-processing: LANCZOS upscale, unsharp masking and a subtle
color grade so generated stills stay crisp and cinematic at full 1080p."""
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter


def postprocess_image(src, dst, target_w, target_h, quality=92):
    """Crop to the target aspect ratio, upscale to target size and sharpen.

    Re-encodes as JPEG 4:4:4 (chroma subsampling off) so edges stay clean.
    """
    src_path = Path(src)
    dst_path = Path(dst)
    im = Image.open(src_path).convert("RGB")

    target_ratio = target_w / target_h
    w, h = im.size
    ratio = w / h

    # Center-crop to the target aspect ratio before resizing.
    if abs(ratio - target_ratio) > 0.012:
        if ratio > target_ratio:
            new_w = int(h * target_ratio)
            left = (w - new_w) // 2
            im = im.crop((left, 0, left + new_w, h))
        else:
            new_h = int(w / target_ratio)
            top = (h - new_h) // 2
            im = im.crop((0, top, w, top + new_h))

    if im.size != (target_w, target_h):
        im = im.resize((target_w, target_h), Image.LANCZOS)

    im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=130, threshold=2))
    im = ImageEnhance.Color(im).enhance(1.10)
    im = ImageEnhance.Contrast(im).enhance(1.04)

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst_path, "JPEG", quality=quality, subsampling=0)  # 4:4:4
    return dst_path