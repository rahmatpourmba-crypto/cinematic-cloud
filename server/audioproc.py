"""Audio post-processing: loudness normalization (broadcast -16 LUFS) and
high-bitrate 44.1 kHz stereo re-encode so narration sounds full and clear.

Uses the ffmpeg binary shipped with imageio-ffmpeg (no system ffmpeg needed).
"""
import shutil
import subprocess
from pathlib import Path


def _ffmpeg() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which("ffmpeg")


def normalize_narration(src, dst, target_sample=44100, bitrate="192k"):
    """Return the output path; falls back to `src` untouched on any failure."""
    src_path = Path(src)
    dst_path = Path(dst)
    ff = _ffmpeg()
    if not ff or src_path == dst_path:
        return src_path

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ff, "-y", "-i", str(src_path), "-vn",
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-ar", str(target_sample), "-ac", "2",
        "-b:a", bitrate, "-c:a", "libmp3lame", str(dst_path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=300)
    except Exception:
        return src_path

    if dst_path.stat().st_size > 0:
        return dst_path
    return src_path