"""Runner entry used from a GitHub Actions runner (or local machine).

Same pipeline as the Cloud Run service, but executed as a plain CLI job so the
GitHub schedule works even before GCP is fully configured.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server import pipeline  # noqa: E402


if __name__ == "__main__":
    pipeline.main()