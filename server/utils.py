"""Small shared helpers: ffprobe duration, app.json loader."""
import json
import re
import subprocess
import sys
from pathlib import Path

from . import config


def ensure_utf8():
    """Re-make stdout/stderr UTF-8 so Persian text prints on any terminal."""
    for stream in (sys.stdout, sys.stderr):
        try:
            if getattr(stream, "encoding", "") and stream.encoding.lower() != "utf-8":
                import io

                replacement = io.TextIOWrapper(
                    stream.buffer, encoding="utf-8", errors="replace"
                )
                if stream is sys.stdout:
                    sys.stdout = replacement
                else:
                    sys.stderr = replacement
        except Exception:  # noqa: BLE001
            pass


def load_app(path: Path = None) -> dict:
    p = path or config.APP_JSON
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def get_story(app: dict, story_id: str) -> dict | None:
    return next((s for s in app["stories"] if s["id"] == story_id), None)


def list_stories(app: dict) -> list[str]:
    return [s["id"] for s in app["stories"]]


def ffprobe_duration(path, default=6.0) -> float:
    path = str(path)
    for cmd in (["ffprobe"],):
        try:
            r = subprocess.run(
                [*cmd, "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", path],
                capture_output=True, text=True, timeout=60,
            )
            if r.returncode == 0:
                m = re.search(r"\d+(\.\d+)?", r.stdout.strip())
                if m:
                    return max(float(m.group()), 1.0)
        except Exception:
            pass
    return default