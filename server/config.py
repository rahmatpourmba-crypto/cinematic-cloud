"""Central config: everything is env-driven so the same tree runs
locally, on a GitHub runner, or inside Cloud Run."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_JSON = ROOT / "app.json"

PUBLIC_DIR = ROOT / "public"
SCENES_DIR = PUBLIC_DIR / "scenes"
AUDIO_DIR = PUBLIC_DIR / "audio"
WORK_DIR = ROOT / ".work"
OUT_DIR = ROOT / "out"

for _d in (SCENES_DIR, AUDIO_DIR, WORK_DIR, OUT_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# --- Google Cloud ---
GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get(
    "GCP_PROJECT", ""
)
VERTEX_LOCATION = os.environ.get("VERTEX_LOCATION", "us-central1")
GCS_BUCKET = os.environ.get("GCS_BUCKET", "")
USE_GOOGLE_IMAGEN = os.environ.get("USE_GOOGLE_IMAGEN", "auto")  # auto|1|0
USE_GOOGLE_TTS = os.environ.get("USE_GOOGLE_TTS", "auto")  # auto|1|0
TTS_VOICE = os.environ.get("TTS_VOICE", "fa-IR-Wavenet-A")
TTS_SPEAKING_RATE = float(os.environ.get("TTS_SPEAKING_RATE", "0.92"))
IMAGEN_MODEL = os.environ.get("IMAGEN_MODEL", "imagen-3.0-generate-002")
IMAGEN_ASPECT = os.environ.get("IMAGEN_ASPECT", "16:9")

# --- API / deploy ---
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
FPS = int(os.environ.get("FPS", "30"))
WIDTH = int(os.environ.get("WIDTH", "1920"))
HEIGHT = int(os.environ.get("HEIGHT", "1080"))
CRF = int(os.environ.get("CRF", "18"))
CONCURRENCY = int(os.environ.get("CONCURRENCY", os.environ.get("CPU_COUNT", "4")))
RENDER_TIMEOUT = int(os.environ.get("RENDER_TIMEOUT", "3300"))

# --- YouTube ---
YOUTUBE_TOKEN_B64 = os.environ.get("YOUTUBE_TOKEN_B64", "")  # base64(pickle credentials)
YOUTUBE_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET", "")
YOUTUBE_REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN", "")
YT_PRIVACY = os.environ.get("YOUTUBE_PRIVACY", "public")
YT_CATEGORY = int(os.environ.get("YOUTUBE_CATEGORY", "27"))


def google_available() -> bool:
    """True when the environment looks like it has GCP credentials."""
    if not GOOGLE_CLOUD_PROJECT:
        return False
    try:
        import google.auth

        creds, _ = google.auth.default()
        return bool(creds and creds.valid)
    except Exception:
        return False