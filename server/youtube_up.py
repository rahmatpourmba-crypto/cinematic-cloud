"""YouTube upload using token provided via environment.

Two ways to authenticate (no local files needed for Cloud Run):
  * YOUTUBE_TOKEN_B64        — base64 of a pickled google.oauth2.credentials.Credentials
                               (what workout/trend-video-maker produced as token_*.pickle)
  * YOUTUBE_CLIENT_ID +
    YOUTUBE_CLIENT_SECRET + YOUTUBE_REFRESH_TOKEN — OAuth refresh token flow
"""
import base64
import pickle
from pathlib import Path

from . import config

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]


def _creds_from_b64() -> object:
    raw = base64.b64decode(config.YOUTUBE_TOKEN_B64)
    creds = pickle.loads(raw)
    return creds


def _creds_from_refresh() -> object:
    from google.oauth2.credentials import Credentials

    creds = Credentials(
        token=None,
        refresh_token=config.YOUTUBE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=config.YOUTUBE_CLIENT_ID,
        client_secret=config.YOUTUBE_CLIENT_SECRET,
        scopes=SCOPES,
    )
    return creds


def build_service():
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    if config.YOUTUBE_TOKEN_B64:
        creds = _creds_from_b64()
    elif config.YOUTUBE_REFRESH_TOKEN and config.YOUTUBE_CLIENT_ID and config.YOUTUBE_CLIENT_SECRET:
        creds = _creds_from_refresh()
    else:
        raise RuntimeError(
            "YouTube auth not configured: set YOUTUBE_TOKEN_B64 or "
            "YOUTUBE_CLIENT_ID/SECRET + YOUTUBE_REFRESH_TOKEN"
        )

    if creds.expired and getattr(creds, "refresh_token", None):
        creds.refresh(Request())
    return build("youtube", "v3", credentials=creds)


def upload_video(yt, video_path: Path, thumb_path: Path,
                 title: str, desc: str, tags=None,
                 privacy: str = None, category_id: int = None,
                 made_for_kids: bool = False) -> str:
    from googleapiclient.http import MediaFileUpload

    privacy = privacy or config.YT_PRIVACY
    category_id = category_id or config.YT_CATEGORY
    body = {
        "snippet": {
            "title": title,
            "description": desc,
            "tags": tags or [],
            "categoryId": str(category_id),
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": made_for_kids,
        },
    }
    media = MediaFileUpload(str(video_path), mimetype="video/mp4", resumable=True)

    request = yt.videos().insert(
        part="snippet,status", body=body, media_body=media
    )
    response = None
    while response is None:
        status, response = request.next_chunk()

    vid = response["id"]
    if thumb_path and Path(thumb_path).exists():
        yt.thumbnails().set(
            videoId=vid,
            media_body=MediaFileUpload(str(thumb_path), mimetype="image/png"),
        ).execute()
    return vid