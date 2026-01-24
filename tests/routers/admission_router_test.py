from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

from dtos.admission import AdmissionCreateDTO, AdmissionDTO, AdmissionUpdateDTO
from routers.admission.admission_router import admission_router, get_admission_repository


class FakeAdmissionRepository:
    def __init__(self):
        self._next_id = 1
        self._records = {}

    def create_admission(self, admission: AdmissionCreateDTO) -> AdmissionDTO:
        data = admission.dict()
        data["id"] = self._next_id
        self._next_id += 1
        dto = AdmissionDTO(**data)
        self._records[dto.id] = dto
        return dto

    def get_admission(self, admission_id: int):
        return self._records.get(admission_id)

    def get_admissions(self, skip: int = 0, limit: int = 100, patient_id: int = 0):
        records = list(self._records.values())
        if patient_id:
            records = [rec for rec in records if rec.patient_id == patient_id]
        return {"data": records[skip:skip + limit], "total": len(records)}

    def update_admission(self, admission_id: int, admission: AdmissionUpdateDTO):
        current = self._records.get(admission_id)
        if not current:
            return None
        data = current.dict()
        data.update(admission.dict(exclude_unset=True))
        updated = AdmissionDTO(**data)
        self._records[admission_id] = updated
        return updated

    def delete_admission(self, admission_id: int):
        return self._records.pop(admission_id, None) is not None


def create_client():
    app = FastAPI()
    app.include_router(admission_router)
    repo = FakeAdmissionRepository()
    app.dependency_overrides[get_admission_repository] = lambda: repo
    return TestClient(app)


def test_admission_crud_flow():
    client = create_client()
    now = datetime.utcnow().isoformat()

    create_resp = client.post(
        "/api/admissions/records",
        json={
            "bed_id": 1,
            "patient_id": 2,
            "admission_date": now,
            "reason": "Observation",
            "user_id": 3,
        },
    )
    assert create_resp.status_code == 201
    admission_id = create_resp.json()["id"]

    get_resp = client.get(f"/api/admissions/records/{admission_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["patient_id"] == 2

    list_resp = client.get("/api/admissions/records?skip=0&limit=10")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    update_resp = client.put(
        f"/api/admissions/records/{admission_id}",
        json={"reason": "Updated"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["reason"] == "Updated"

    delete_resp = client.delete(f"/api/admissions/records/{admission_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["deleted"] is True

    missing_resp = client.get(f"/api/admissions/records/{admission_id}")
    assert missing_resp.status_code == 404
