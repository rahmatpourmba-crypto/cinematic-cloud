"""Persian narration synthesis.

Primary path: Google Cloud Text-to-Speech (fa-IR-Wavenet-A, MP3).
Automatic fallback: edge-tts (fa-IR-FaridNeural) so it works offline / free.
"""
import asyncio
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
    import edge_tts

    async def _run():
        data = b""
        async for chunk in edge_tts.Communicate(
            text, "fa-IR-FaridNeural", rate="-12%"
        ).stream():
            if chunk["type"] == "audio":
                data += chunk["data"]
        return data

    for attempt in range(4):
        try:
            data = asyncio.run(_run())
            if data:
                out_path.write_bytes(data)
                return out_path
        except Exception:  # noqa: BLE001
            pass
        time.sleep(5 * (attempt + 1))
    raise RuntimeError("edge-tts failed")


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