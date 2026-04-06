import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb")

from routers.upload_router import upload_router
from security.dependencies import get_current_active_user
from storage import UPLOADS_DIR


def create_client():
    app = FastAPI()
    app.include_router(upload_router)
    app.dependency_overrides[get_current_active_user] = lambda: {"id": 1}
    return TestClient(app)


def test_uploaded_config_image_is_served_from_all_supported_paths():
    client = create_client()
    upload_dir = UPLOADS_DIR / "img" / "config"
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = "test-config-image.png"
    file_path = upload_dir / filename
    file_path.write_bytes(b"png-data")

    try:
        for path in (
            f"/uploads/img/config/{filename}",
            f"/api/uploads/img/config/{filename}",
            f"/img/config/{filename}",
            f"/api/img/config/{filename}",
        ):
            response = client.get(path)
            assert response.status_code == 200
            assert response.content == b"png-data"
    finally:
        if file_path.exists():
            file_path.unlink()
