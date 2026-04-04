import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = Path(os.getenv("UPLOADS_DIR", BASE_DIR / "uploads")).resolve()
