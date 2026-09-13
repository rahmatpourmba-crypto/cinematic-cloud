"""Cinematic image generation.

Primary path: Vertex AI Imagen (paid, photorealistic, 4K capable).
Automatic fallback: Pollinations.ai flux (free) so the pipeline always works
even without GCP credentials.
"""
import time
from pathlib import Path
from urllib.parse import quote

import requests

from . import config


def _fallback_to_google() -> bool:
    if config.USE_GOOGLE_IMAGEN == "1":
        return True
    if config.USE_GOOGLE_IMAGEN == "0":
        return False
    return config.google_available()


def _imagen(prompt: str, out_path: Path, seed: int, width: int, height: int) -> Path:
    from vertexai.preview.vision_models import ImageGenerationModel

    model = ImageGenerationModel.from_pretrained(config.IMAGEN_MODEL)
    kwargs = dict(
        prompt=prompt,
        number_of_images=1,
        aspect_ratio=config.IMAGEN_ASPECT,
        add_watermark=False,
        output_mime_type="image/jpeg",
    )
    try:
        kwargs["seed"] = seed
        images = model.generate_images(**kwargs)
    except TypeError:
        kwargs.pop("seed", None)
        images = model.generate_images(**kwargs)
    if not images:
        raise RuntimeError("Imagen returned no images")
    images[0].save(str(out_path))
    return out_path


def _pollinations(prompt: str, out_path: Path, seed: int, width: int, height: int) -> Path:
    url = (
        "https://image.pollinations.ai/prompt/"
        f"{quote(prompt)}?width={width}&height={height}&seed={seed}"
        f"&nologo=true&model=flux"
    )
    last = None
    for i in range(4):
        try:
            r = requests.get(url, timeout=240)
            if r.status_code == 200 and len(r.content) > 5000:
                out_path.write_bytes(r.content)
                return out_path
            last = f"HTTP {r.status_code}"
        except Exception as e:  # noqa: BLE001
            last = str(e)
        time.sleep(3 * (i + 1))
    raise RuntimeError(f"pollinations failed: {last}")


def generate_image(prompt: str, out_path: Path, seed: int,
                   width: int = None, height: int = None,
                   force=False) -> Path:
    out_path = Path(out_path)
    if not force and out_path.exists() and out_path.stat().st_size > 0:
        return out_path

    width = width or config.WIDTH
    height = height or config.HEIGHT

    if _fallback_to_google():
        try:
            print(f"  [imagen] generating {out_path.name} (seed={seed})", flush=True)
            return _imagen(prompt, out_path, seed, width, height)
        except Exception as e:  # noqa: BLE001
            print(f"  [imagen] failed ({type(e).__name__}: {e}) -> pollinations", flush=True)

    print(f"  [pollinations] generating {out_path.name} (seed={seed})", flush=True)
    return _pollinations(prompt, out_path, seed, width, height)