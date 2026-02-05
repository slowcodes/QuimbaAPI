import os

from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb")

from dtos.people import ReferralDTO, PersonDTO, ReferralResponseDTO
from routers.client.referral_router import (
    referral_router,
    get_referral_repository,
    get_people_repository,
    get_organization_repository,
)


class FakeReferralRepository:
    def __init__(self):
        self._next_id = 1
        self._referrals = {}

    def create(self, person_id: int) -> ReferralDTO:
        referral = ReferralDTO(id=self._next_id, person_id=person_id, person=None)
        self._referrals[self._next_id] = referral
        self._next_id += 1
        return referral

    def get(self, referral_id: int):
        return self._referrals.get(referral_id)

    def get_all_referrals(self, skip: int = 0, limit: int = 10, search_text: str = "") -> ReferralResponseDTO:
        data = list(self._referrals.values())
        return ReferralResponseDTO(data=data[skip: skip + limit], total=len(data))

    def update_referral(self, referral_id: int, referral_data: ReferralDTO):
        current = self._referrals.get(referral_id)
        if not current:
            return None
        data = current.dict()
        if referral_data.person_id is not None:
            data["person_id"] = referral_data.person_id
        if referral_data.person is not None:
            data["person"] = referral_data.person
        updated = ReferralDTO(**data)
        self._referrals[referral_id] = updated
        return updated

    def soft_delete(self, referral_id: int) -> bool:
        return self._referrals.pop(referral_id, None) is not None


class FakePersonRepository:
    def __init__(self):
        self._next_id = 1
        self._people = {}

    def person_exists(self, person_dto: PersonDTO) -> bool:
        return False

    def create(self, person_dto: PersonDTO):
        data = person_dto.dict()
        data["id"] = self._next_id
        self._next_id += 1
        person = PersonDTO(**data)
        self._people[person.id] = person
        return person


class FakeOrganizationRepository:
    pass


def create_client():
    app = FastAPI()
    app.include_router(referral_router)
    referral_repo = FakeReferralRepository()
    person_repo = FakePersonRepository()
    app.dependency_overrides[get_referral_repository] = lambda: referral_repo
    app.dependency_overrides[get_people_repository] = lambda: person_repo
    app.dependency_overrides[get_organization_repository] = lambda: FakeOrganizationRepository()
    return TestClient(app), referral_repo


def test_referral_crud_flow():
    client, repo = create_client()

    payload = {
        "person": {
            "title": "Mr",
            "first_name": "John",
            "middle_name": "Q",
            "last_name": "Public",
            "sex": "Male",
            "email": "john@example.com",
            "phone": "08012345678",
        }
    }

    create_resp = client.post("/api/clients/referral/", json=payload)
    assert create_resp.status_code == 200

    referral_id = next(iter(repo._referrals))

    get_resp = client.get(f"/api/clients/referral/{referral_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == referral_id

    list_resp = client.get("/api/clients/referral/?page=0&limit=10")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    update_payload = {
        "person": {
            "title": "Dr",
            "first_name": "Jane",
            "middle_name": "R",
            "last_name": "Public",
            "sex": "Female",
            "email": "jane@example.com",
            "phone": "08011112222",
        }
    }
    update_resp = client.put(f"/api/clients/referral/{referral_id}", json=update_payload)
    assert update_resp.status_code == 200
    assert update_resp.json()["person"]["first_name"] == "Jane"

    delete_resp = client.delete(f"/api/clients/referral/{referral_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["success"] is True
