"""Google Cloud Storage helpers for caching generated assets + output videos.

If GCS_BUCKET is not configured (or no credentials), everything stays local —
the pipeline is fully functional without GCP.
"""
from pathlib import Path

from . import config


def _client():
    from google.cloud import storage

    return storage.Client(project=config.GOOGLE_CLOUD_PROJECT)


def enabled() -> bool:
    if not config.GCS_BUCKET:
        return False
    try:
        _client().bucket(config.GCS_BUCKET)
        return True
    except Exception:
        return False


def upload_file(local_path: Path, blob_name: str, public=False) -> str:
    """Upload a file and return its URL."""
    local_path = Path(local_path)
    if not enabled() or not local_path.exists():
        return str(local_path)
    client = _client()
    bucket = client.bucket(config.GCS_BUCKET)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(str(local_path), content_type="application/octet-stream")
    if public:
        blob.make_public()
        return blob.public_url
    return f"gs://{config.GCS_BUCKET}/{blob_name}"


def get_cached(blob_name: str, local_path: Path) -> bool:
    """Download existing blob into local cache if available."""
    if not enabled():
        return False
    try:
        client = _client()
        bucket = client.bucket(config.GCS_BUCKET)
        blob = bucket.blob(blob_name)
        if not blob.exists():
            return False
        local_path.parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(str(local_path))
        return True
    except Exception:
        return False