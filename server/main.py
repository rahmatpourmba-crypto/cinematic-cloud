"""Cloud Run API — cinematic pipeline + prompt studio over HTTP.

Story pipeline (GitHub Actions schedule / cron):
    curl -X POST $CINEMATIC_URL/render -H "X-Webhook-Secret: $SECRET" \
         -d '{"story_id":"solomon_hoopoe","episode":2,"upload":true}'

Prompt studio (web UI):
    GET  /                         -> index.html
    POST /api/generate             -> {"job_id": "..."}
    GET  /api/jobs/{job_id}        -> status + /media/<file> when done
"""
import os

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import config, pipeline, studio
from .utils import get_story, list_stories, load_app

app = FastAPI(title="Cinematic Cloud", version="2.0.0")

STUDIO_DIR = config.ROOT / "public" / "studio"


class RenderRequest(BaseModel):
    story_id: str | None = Field(default=None)
    episode: int = Field(default=1, ge=1)
    upload: bool = False
    force: bool = False


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=8, max_length=4000)
    style: str = Field(default="cinematic",
                       pattern="^(cinematic|fantasy|docu|islamic)$")
    quality: str = Field(default="full", pattern="^(hd|full)$")


def _check_secret(x_webhook_secret: str | None):
    if config.WEBHOOK_SECRET and x_webhook_secret != config.WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="bad webhook secret")


@app.get("/")
def index():
    index_html = STUDIO_DIR / "index.html"
    if index_html.exists():
        return FileResponse(index_html)
    return {"app": "cinematic-cloud", "docs": "/docs"}


@app.get("/health")
def health():
    return {
        "ok": True,
        "stories": list_stories(load_app()),
        "google_available": config.google_available(),
        "studio": STUDIO_DIR.exists(),
    }


@app.post("/api/generate")
def api_generate(req: GenerateRequest):
    job = studio.create_job(req.prompt)
    studio.generate_async(job, req.prompt, req.style, req.quality)
    return {"job_id": job["id"]}


@app.get("/api/jobs/{job_id}")
def api_job(job_id: str):
    job = studio.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="unknown job")
    return job


@app.get("/api/jobs")
def api_jobs():
    return {"jobs": studio.job_list()}


@app.post("/render")
def render(req: RenderRequest, x_webhook_secret: str | None = Header(default=None)):
    _check_secret(x_webhook_secret)
    ad = load_app()
    story = get_story(ad, req.story_id) if req.story_id else None
    if req.story_id and not story:
        raise HTTPException(status_code=404, detail=f"unknown story: {req.story_id}")
    try:
        res = pipeline.run_story(
            ad, story, req.episode, upload_yt=req.upload, force=req.force
        )
        return res
    except Exception as e:  # noqa: BLE001
        import traceback

        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/render-all")
def render_all(x_webhook_secret: str | None = Header(default=None)):
    _check_secret(x_webhook_secret)
    ad = load_app()
    results = []
    for s in ad["stories"]:
        try:
            results.append(pipeline.run_story(ad, s, 1, upload_yt=False))
        except Exception as e:  # noqa: BLE001
            results.append({"story_id": s["id"], "error": str(e)})
    return {"results": results}


# Serve generated videos / stills + studio assets.
app.mount("/media", StaticFiles(directory=str(config.OUT_DIR)), name="media")
app.mount("/studio", StaticFiles(directory=str(STUDIO_DIR)), name="studio")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)