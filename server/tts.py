"""Persian narration synthesis.

Priority: Google Cloud Text-to-Speech (Neural2/Chirp, MP3) when GCP
credentials are available; automatic fallback to edge-tts so the pipeline
always works offline / free.

edge-tts runs inside a fresh subprocess (scripts/tts_once.py) to isolate
its async/websocket stack from the Uvicorn event loop on Windows — the
in-process variant intermittently fails with NoAudioReceived there.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

from . import config


def _fallback_to_google() -> bool:
    if config.USE_GOOGLE_TTS == "1":
        return True
    if config.USE_GOOGLE_TTS == "0":
        return False
    return config.google_available()


def _google_tts(text: str, out_path: Path) -> Path:
    from google.cloud import texttospeech

    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="fa-IR",
        name=config.TTS_VOICE,
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=config.TTS_SPEAKING_RATE,
        pitch=0.0,
    )
    resp = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    if not resp.audio_content:
        raise RuntimeError("Google TTS produced empty audio")
    out_path.write_bytes(resp.audio_content)
    return out_path


def _edge_tts(text: str, out_path: Path) -> Path:
    from .audioproc import normalize_narration

    helper = config.ROOT / "scripts" / "tts_once.py"
    last = None
    for attempt in range(4):
        raw = out_path.with_suffix(".raw.mp3")
        dbg = config.WORK_DIR / f"tts_dbg_{out_path.stem}.txt"
        try:
            proc = subprocess.run(
                [sys.executable, str(helper), str(raw), str(dbg)],
                input=text, text=True, encoding="utf-8", capture_output=True,
                timeout=300, cwd=str(config.ROOT),
            )
            if dbg.exists():
                print(f"  [edge-tts] dbg: {dbg.read_text(encoding='utf-8', errors='replace').strip()}"[:500], flush=True)
            if proc.returncode == 0 and raw.exists() and raw.stat().st_size > 0:
                normalize_narration(raw, out_path)
                raw.unlink(missing_ok=True)
                return out_path
            last = (proc.stderr or "").strip()[-400:] or f"exit={proc.returncode}"
        except Exception as e:  # noqa: BLE001
            last = f"attempt {attempt + 1}: {type(e).__name__}: {e}"
        print(f"  [edge-tts] {last}", flush=True)
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"edge-tts failed ({last})")


def synthesize(text: str, out_path: Path, force=False) -> Path:
    out_path = Path(out_path)
    if not force and out_path.exists() and out_path.stat().st_size > 0:
        return out_path

    if _fallback_to_google():
        try:
            print(f"  [gc-tts] synthesizing {out_path.name}", flush=True)
            return _google_tts(text, out_path)
        except Exception as e:  # noqa: BLE001
            print(f"  [gc-tts] failed ({type(e).__name__}: {e}) -> edge-tts", flush=True)

    print(f"  [edge-tts] synthesizing {out_path.name}", flush=True)
    return _edge_tts(text, out_path)