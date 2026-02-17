import os

from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb")

from dtos.conf import ConfSettingDTO
from models.conf import DataType, UIControlType
from routers.security_router import security_router, conf_repo
from security.dependencies import get_current_active_user


class FakeSettingRepository:
    def __init__(self):
        self._next_id = 1
        self._settings = {}

    def create_setting(self, setting: ConfSettingDTO) -> ConfSettingDTO:
        data = setting.dict()
        data["id"] = self._next_id
        self._next_id += 1
        dto = ConfSettingDTO(**data)
        self._settings[dto.id] = dto
        return dto

    def get_settings(self, skip: int = 0, limit: int = 100):
        data = list(self._settings.values())
        return data[skip:skip + limit]

    def get_setting(self, setting_id: int):
        return self._settings.get(setting_id)

    def update_setting(self, setting_id: int, setting: ConfSettingDTO):
        current = self._settings.get(setting_id)
        if not current:
            return None
        data = setting.dict()
        data["id"] = setting_id
        dto = ConfSettingDTO(**data)
        self._settings[setting_id] = dto
        return dto

    def delete_setting(self, setting_id: int) -> bool:
        return self._settings.pop(setting_id, None) is not None


def create_client(authenticated: bool = True):
    app = FastAPI()
    app.include_router(security_router)
    repo = FakeSettingRepository()
    app.dependency_overrides[conf_repo] = lambda: repo
    if authenticated:
        app.dependency_overrides[get_current_active_user] = lambda: {"id": 1}
    return TestClient(app)


def test_conf_setting_requires_authentication():
    client = create_client(authenticated=False)
    response = client.get("/api/v1/auth/config/setting")
    assert response.status_code == 401


def test_conf_setting_crud_flow():
    client = create_client(authenticated=True)

    payload = {
        "parameter": "logo_url",
        "data_type": DataType.String.value,
        "param_value": "https://example.com/logo.png",
        "ui_control_type": UIControlType.TextField.value,
    }

    create_resp = client.post("/api/v1/auth/config/setting", json=payload)
    assert create_resp.status_code == 201
    setting_id = create_resp.json()["id"]

    get_resp = client.get(f"/api/v1/auth/config/setting/{setting_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["parameter"] == "logo_url"

    list_resp = client.get("/api/v1/auth/config/setting?skip=0&limit=10")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    update_resp = client.put(
        f"/api/v1/auth/config/setting/{setting_id}",
        json={
            "parameter": "logo_url",
            "data_type": DataType.String.value,
            "param_value": "https://example.com/new-logo.png",
            "ui_control_type": UIControlType.TextField.value,
        },
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["param_value"] == "https://example.com/new-logo.png"

    delete_resp = client.delete(f"/api/v1/auth/config/setting/{setting_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["deleted"] is True

    missing_resp = client.get(f"/api/v1/auth/config/setting/{setting_id}")
    assert missing_resp.status_code == 404
