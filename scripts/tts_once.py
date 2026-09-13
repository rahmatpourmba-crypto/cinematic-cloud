"""Synthesize one narration clip via edge-tts inside a fresh process.

The server keeps async/websocket work (edge-tts) isolated from the Uvicorn
event loop so a flaky synthesis can never destabilise the long-running
service. Reads text on stdin, writes raw MP3 to argv[1].
"""
import asyncio
import os
import sys
from pathlib import Path

VOICE = os.environ.get("TTS_FALLBACK_VOICE", "fa-IR-DilaraNeural")
RATE = os.environ.get("TTS_RATE", "-4%")


async def _stream(text: str) -> bytes:
    import edge_tts

    data = b""
    async for chunk in edge_tts.Communicate(text, VOICE, rate=RATE).stream():
        if chunk["type"] == "audio":
            data += chunk["data"]
    return data


def main():
    text = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    dbg = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    if dbg:
        dbg.write_text(
            f"len={len(text)}\nvoice={VOICE}\nrate={RATE}\n"
            f"repr={text[:120]!r}\nhex0={text[:40].encode('utf-8').hex()}\n",
            encoding="utf-8",
        )
    out = Path(sys.argv[1])
    data = asyncio.run(_stream(text))
    if not data:
        sys.exit(3)
    out.write_bytes(data)


if __name__ == "__main__":
    main()