"""Thin wrapper over the Remotion CLI (render + still to PNG)."""
import json
import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path

from . import config

NODE_MODULES_BIN = config.ROOT / "node_modules" / ".bin"


def _npx() -> str:
    candidates = [
        NODE_MODULES_BIN / ("npx.cmd" if os.name == "nt" else "npx"),
        NODE_MODULES_BIN / "npx",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    found = shutil.which("npx") or shutil.which("npx.cmd")
    if not found:
        raise RuntimeError("npx not found — run `npm ci` in the project first")
    return found


def _run(cmd: list[str], log_prefix: str, timeout: int):
    print(f"  [{log_prefix}] running: {' '.join(cmd[:6])} ...", flush=True)
    t0 = time.time()
    env = dict(os.environ)
    env.setdefault("REMOTION_EXECUTABLE", str(config.ROOT / "node_modules" / ".bin" / "remotion"))
    proc = subprocess.run(
        cmd, cwd=str(config.ROOT), env=env,
        capture_output=True, text=True, timeout=timeout,
    )
    out = (proc.stdout or "")[-4000:]
    err = (proc.stderr or "")[-4000:]
    print(f"  [{log_prefix}] exit={proc.returncode} ({time.time() - t0:.0f}s)", flush=True)
    if proc.stdout:
        print(out, flush=True)
    if proc.stderr:
        print(f"  [{log_prefix} stderr]\n{err}", flush=True)
    if proc.returncode != 0:
        raise RuntimeError(f"{log_prefix} failed ({proc.returncode})")


def _props_file(props: dict) -> Path:
    p = config.WORK_DIR / f"props_{uuid.uuid4().hex[:10]}.json"
    p.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    return p


def render_video(props: dict, out_path: Path,
                 fps: int = None, crf: int = None,
                 composition: str = "CinematicStory") -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()
    props_file = _props_file(props)
    fps = fps or config.FPS
    crf = crf if crf is not None else config.CRF
    cmd = [
        _npx(), "remotion", "render",
        "src/index.ts", composition, str(out_path),
        "--props", str(props_file),
        "--codec=h264", "--crf", str(crf),
        "--fps", str(fps), "--pixel-format=yuv420p",
        "--concurrency", str(config.CONCURRENCY),
        "--log=info",
    ]
    _run(cmd, "render", config.RENDER_TIMEOUT)
    return out_path


def render_still(props: dict, out_path: Path, composition: str = "StoryThumbnail") -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()
    props_file = _props_file(props)
    cmd = [
        _npx(), "remotion", "still",
        "src/index.ts", composition, str(out_path),
        "--props", str(props_file),
        "--frame=0", "--image-format=png",
        "--log=info",
    ]
    _run(cmd, "still", config.RENDER_TIMEOUT)
    return out_path