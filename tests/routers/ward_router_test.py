from fastapi import FastAPI
from fastapi.testclient import TestClient

from dtos.admission import WardCreateDTO, WardDTO, WardUpdateDTO
from routers.admission.ward_router import ward_router, get_ward_repository


class FakeWardRepository:
    def __init__(self):
        self._next_id = 1
        self._wards = {}

    def create_ward(self, ward: WardCreateDTO) -> WardDTO:
        data = ward.dict()
        data["id"] = self._next_id
        self._next_id += 1
        dto = WardDTO(**data)
        self._wards[dto.id] = dto
        return dto

    def get_ward(self, ward_id: int):
        return self._wards.get(ward_id)

    def get_wards(self, skip: int = 0, limit: int = 100):
        wards = list(self._wards.values())
        return {"data": wards[skip:skip + limit], "total": len(wards)}

    def update_ward(self, ward_id: int, ward: WardUpdateDTO):
        current = self._wards.get(ward_id)
        if not current:
            return None
        data = current.dict()
        data.update(ward.dict(exclude_unset=True))
        updated = WardDTO(**data)
        self._wards[ward_id] = updated
        return updated

    def delete_ward(self, ward_id: int):
        return self._wards.pop(ward_id, None) is not None


def create_client():
    app = FastAPI()
    app.include_router(ward_router)
    repo = FakeWardRepository()
    app.dependency_overrides[get_ward_repository] = lambda: repo
    return TestClient(app)


def test_ward_crud_flow():
    client = create_client()

    create_resp = client.post(
        "/api/admissions/wards",
        json={"name": "Ward A", "description": "Primary ward", "ward_type": "General"},
    )
    assert create_resp.status_code == 201
    ward_id = create_resp.json()["id"]

    get_resp = client.get(f"/api/admissions/wards/{ward_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Ward A"

    list_resp = client.get("/api/admissions/wards?skip=0&limit=10")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    update_resp = client.put(
        f"/api/admissions/wards/{ward_id}",
        json={"name": "Ward B"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Ward B"

    delete_resp = client.delete(f"/api/admissions/wards/{ward_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["deleted"] is True

    missing_resp = client.get(f"/api/admissions/wards/{ward_id}")
    assert missing_resp.status_code == 404
