"""Cloud Run API — triggers the cinematic pipeline over HTTP.

Call it from GitHub Actions schedule or cron with the webhook secret header:

    curl -X POST $CINEMATIC_URL/render -H "X-Webhook-Secret: $SECRET" \
         -d '{"story_id":"solomon_hoopoe","episode":2,"upload":true}'
"""
import os

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from . import config, pipeline
from .utils import get_story, list_stories, load_app

app = FastAPI(title="Cinematic Cloud", version="1.0.0")


class RenderRequest(BaseModel):
    story_id: str | None = Field(default=None)
    episode: int = Field(default=1, ge=1)
    upload: bool = False
    force: bool = False


def _check_secret(x_webhook_secret: str | None):
    if config.WEBHOOK_SECRET and x_webhook_secret != config.WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="bad webhook secret")


@app.get("/")
def root():
    return {"app": "cinematic-cloud", "docs": "/docs"}


@app.get("/health")
def health():
    return {
        "ok": True,
        "stories": list_stories(load_app()),
        "google_available": config.google_available(),
    }


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


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)