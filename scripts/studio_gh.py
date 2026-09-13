"""Headless studio renderer for the GitHub Actions flow.

Reads a job payload (JSON) written by the web UI / issue body, runs the exact
same studio pipeline as the local server, and writes result metadata for the
workflow to publish to gh-pages.

Usage: python scripts/studio_gh.py <payload.json>
"""
import json
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server import config, studio  # noqa: E402


def main() -> int:
    payload_path = Path(sys.argv[1])
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    jid = payload.get("id") or studio.create_job(payload.get("prompt", ""))["id"]

    job = {
        "id": jid,
        "status": "queued",
        "stage": "",
        "progress": 0,
        "message": "",
        "prompt": payload.get("prompt", ""),
        "error": None,
        "video": None,
        "thumbnail": None,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Mirror job progress to stdout so the workflow log is informative.
    orig_update = studio._update
    def log_update(j, **fields):
        orig_update(j, **fields)
        print(f"[job] {j.get('stage', '')} | {j.get('progress', 0):>3}%",
              flush=True)
    studio._update = log_update

    result = {"id": jid, "prompt": payload.get("prompt", "")}
    try:
        studio._run_job(
            job,
            payload["prompt"],
            payload.get("style", "cinematic"),
            payload.get("quality", "hd"),
        )
        vname = Path(job["video"]).name
        tname = Path(job["thumbnail"]).name
        result.update(
            status="done",
            video=vname,
            poster=tname,
            created=job["created_at"],
            stage="done",
        )
    except Exception as e:  # noqa: BLE001
        traceback.print_exc()
        result.update(status="failed", error=str(e))
        return 1

    out = ROOT / ".studio_artifacts.json"
    out.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())