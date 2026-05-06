import os
from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb")

from dtos.auth import UserDTO
from dtos.lab import (
    LabObservationResultTemplateCreateDTO,
    LabObservationResultTemplateDTO,
    LabObservationResultTemplateUpdateDTO,
)
from routers.lab.observation_result_template_router import (
    get_observation_result_template_repository,
    observation_result_template_router,
)
from security.dependencies import get_current_active_user


class FakeObservationResultTemplateRepository:
    def __init__(self):
        self._next_id = 1
        self._templates = {}
        self.created_by = None

    def create_template(
        self,
        template: LabObservationResultTemplateCreateDTO,
        created_by: int,
    ) -> LabObservationResultTemplateDTO:
        self.created_by = created_by
        data = template.model_dump()
        data.update(
            id=self._next_id,
            created_by=created_by,
            created_at=datetime(2026, 5, 6),
            user={"id": created_by, "username": "tester"},
        )
        self._next_id += 1
        dto = LabObservationResultTemplateDTO(**data)
        self._templates[dto.id] = dto
        return dto

    def get_template(self, template_id: int):
        return self._templates.get(template_id)

    def get_templates(self, skip: int = 0, limit: int = 100, search_text: str = ""):
        if search_text:
            return self.search_templates(search_text=search_text, skip=skip, limit=limit)
        templates = list(self._templates.values())
        return {"data": templates[skip:skip + limit], "total": len(templates)}

    def search_templates(self, search_text: str, skip: int = 0, limit: int = 100):
        lowered = search_text.lower()
        templates = [
            template
            for template in self._templates.values()
            if lowered in (template.template or "").lower()
            or lowered in (template.template_desc or "").lower()
        ]
        return {"data": templates[skip:skip + limit], "total": len(templates)}

    def update_template(
        self,
        template_id: int,
        template: LabObservationResultTemplateUpdateDTO,
    ):
        current = self._templates.get(template_id)
        if not current:
            return None
        data = current.model_dump()
        data.update(template.model_dump(exclude_unset=True))
        updated = LabObservationResultTemplateDTO(**data)
        self._templates[template_id] = updated
        return updated

    def delete_template(self, template_id: int):
        return self._templates.pop(template_id, None) is not None


def create_client():
    app = FastAPI()
    app.include_router(observation_result_template_router)
    repo = FakeObservationResultTemplateRepository()
    app.dependency_overrides[get_observation_result_template_repository] = lambda: repo
    app.dependency_overrides[get_current_active_user] = lambda: UserDTO(id=99, username="tester")
    return TestClient(app), repo


def test_observation_result_template_crud_and_search_flow():
    client, repo = create_client()

    create_resp = client.post(
        "/api/laboratories/observation-result-templates/",
        json={"template": "Normal observation", "template_desc": "Radiology"},
    )
    assert create_resp.status_code == 201
    assert create_resp.json()["created_by"] == 99
    assert create_resp.json()["user"]["username"] == "tester"
    assert repo.created_by == 99
    template_id = create_resp.json()["id"]

    get_resp = client.get(f"/api/laboratories/observation-result-templates/{template_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["template"] == "Normal observation"

    search_resp = client.get(
        "/api/laboratories/observation-result-templates/search?search_text=radiology"
    )
    assert search_resp.status_code == 200
    assert search_resp.json()["total"] == 1

    update_resp = client.put(
        f"/api/laboratories/observation-result-templates/{template_id}",
        json={"template_desc": "Updated radiology"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["template_desc"] == "Updated radiology"

    delete_resp = client.delete(
        f"/api/laboratories/observation-result-templates/{template_id}"
    )
    assert delete_resp.status_code == 200
    assert delete_resp.json()["deleted"] is True

    missing_resp = client.get(f"/api/laboratories/observation-result-templates/{template_id}")
    assert missing_resp.status_code == 404
