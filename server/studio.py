"""Prompt studio: turn a free-form prompt into a cinematic video.

Pipeline: split the prompt into scenes -> generate one image per scene ->
synthesize one narration clip per scene (Google Neural TTS when available,
edge-tts fallback) -> Remotion render -> thumbnail.

Jobs live in memory (single-instance services only) with a JSON status that
the web UI polls.
"""
import re
import threading
import time
import traceback
import uuid
from pathlib import Path

from . import config, renderer
from .assetgen import generate_image
from .tts import synthesize

STYLE_SUFFIX = {
    "cinematic": (
        "highly cinematic, dramatic golden-hour lighting, ultra detailed, "
        "4k, photorealistic, epic film still, shallow depth of field, "
        "cinematic color grading, volumetric light"
    ),
    "fantasy": (
        "epic fantasy painting, ethereal glow, rich colors, highly detailed, "
        "magical atmosphere, painterly concept art style"
    ),
    "docu": (
        "documentary photography, natural soft light, realistic textures, "
        "editorial photo style, high dynamic range, sharp focus"
    ),
    "islamic": (
        "islamic art aesthetic, gold and navy palette, ornate geometric "
        "patterns, majestic and reverent atmosphere, cinematic, ultra detailed"
    ),
}

QUALITY_PRESETS = {
    "hd": {"width": 1280, "height": 720, "crf": 20},
    "full": {"width": 1920, "height": 1080, "crf": 17},
}

_PUNCT_SPLIT = re.compile(r"(?<=[.!؟?])|\n")


def _sentences(text: str) -> list[str]:
    text = " ".join(text.split())
    return [s.strip() for s in _PUNCT_SPLIT.split(text) if s.strip()]


def split_scenes(text: str, max_scenes: int = 4, max_chars: int = 180) -> list[str]:
    """Pack sentences into narration scenes of roughly equal spoken length."""
    sentences = _sentences(text) or ([text.strip()] if text.strip() else [])
    scenes: list[str] = []
    cur = ""
    for s in sentences:
        if cur and len(cur) + len(s) + 1 > max_chars:
            scenes.append(cur.strip())
            cur = s
        else:
            cur += (" " if cur else "") + s
    if cur.strip():
        scenes.append(cur.strip())
    while len(scenes) > max_scenes:
        tail = scenes.pop()
        scenes[-1] = f"{scenes[-1]} {tail}"
    return scenes


_LOCK = threading.RLock()
_JOBS: dict[str, dict] = {}


def _update(job: dict, **fields) -> None:
    with _LOCK:
        job.update(fields)


def create_job(prompt: str) -> dict:
    with _LOCK:
        job = {
            "id": uuid.uuid4().hex[:12],
            "status": "queued",
            "stage": "در صف…",
            "progress": 0,
            "message": "",
            "prompt": prompt,
            "error": None,
            "video": None,
            "thumbnail": None,
            "created_at": time.strftime("%H:%M:%S"),
        }
        _JOBS[job["id"]] = job
        return job


def get_job(job_id: str) -> dict | None:
    with _LOCK:
        return _JOBS.get(job_id)


def job_list() -> list[dict]:
    with _LOCK:
        return [_JOBS[k] for k in list(_JOBS.keys())[-10:][::-1]]


def generate_async(job: dict, prompt: str, style: str, quality: str) -> None:
    def run():
        try:
            _run_job(job, prompt, style, quality)
        except Exception as e:  # noqa: BLE001
            _update(job, status="failed", message=str(e),
                    error=traceback.format_exc())

    threading.Thread(target=run, daemon=True).start()


def _title_of(text: str) -> str:
    sentences = _sentences(text)
    title = sentences[0] if sentences else text
    words = title.split()
    return " ".join(words[:9])


def _run_job(job: dict, prompt: str, style: str, quality: str) -> None:
    title = _title_of(prompt)
    scenes = split_scenes(prompt)
    preset = QUALITY_PRESETS.get(quality, QUALITY_PRESETS["full"])
    suffix = STYLE_SUFFIX.get(style, STYLE_SUFFIX["cinematic"])
    jid = job["id"]

    _update(job, status="running",
            stage=f"پردازش متن… ({len(scenes)} صحنه)", progress=4)

    assets: list[dict] = []
    total = len(scenes) + 2
    for i, s in enumerate(scenes):
        name = f"studio_{jid}_c{i}"
        img = config.SCENES_DIR / f"{name}.jpg"
        aud = config.AUDIO_DIR / f"{name}.mp3"
        seed = 7000 + (sum(map(ord, jid[:6])) % 900) + i * 7

        _update(job, stage=f"تولید تصویر {i + 1} از {len(scenes)}…",
                progress=4 + int((i / total) * 60))
        generate_image(f"{s} — {suffix}", img, seed,
                       width=preset["width"], height=preset["height"])

        _update(job, stage=f"ساخت روایت {i + 1} از {len(scenes)}…",
                progress=4 + int(((i + 0.5) / total) * 60))
        synthesize(s, aud)

        from .utils import ffprobe_duration
        dur = ffprobe_duration(aud)
        assets.append({
            "image": f"/scenes/{name}.jpg",
            "audio": f"/audio/{name}.mp3",
            "title": f"صحنه {i + 1}",
            "caption": s,
            "seconds": dur + 0.6,
        })

    props = {
        "storyTitleFa": title,
        "storyTitleEn": "AI STORY",
        "episode": 1,
        "series": "قصه‌نگار | Prompt Studio",
        "subscribeText": "این ویدیو با هوش مصنوعی ساخته شد",
        "scenes": assets,
        "fps": config.FPS,
    }
    video_path = config.OUT_DIR / f"studio_{jid}_cinematic.mp4"
    thumb_path = config.OUT_DIR / f"studio_{jid}_thumb.png"

    _update(job, stage="رندر ویدیو… (چند دقیقه)", progress=70)
    renderer.render_video(props, video_path,
                          fps=config.FPS, crf=preset["crf"])

    _update(job, stage="ساخت تصویر بندانگشتی…", progress=96)
    renderer.render_still({
        "image": assets[0]["image"],
        "faTitle": title,
        "enTitle": "AI STORY",
        "episode": 1,
        "series": "قصه‌نگار | Prompt Studio",
    }, thumb_path)

    _update(job, status="done", stage="آماده", progress=100,
            video=f"/media/{video_path.name}",
            thumbnail=f"/media/{thumb_path.name}")


def generate_sync(prompt: str, style: str = "cinematic",
                  quality: str = "hd") -> dict:
    """Blocking variant used by CLI smoke tests."""
    job = create_job(prompt)
    generate_async(job, prompt, style, quality)
    while get_job(job["id"])["status"] in ("queued", "running"):
        time.sleep(2)
    return get_job(job["id"])