import os

from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb")

from dtos.auth import UserDTO
from routers.lab.lab_router import lab_router
from security.dependencies import get_current_active_user


def create_client():
    app = FastAPI()
    app.include_router(lab_router)
    app.dependency_overrides[get_current_active_user] = lambda: UserDTO(id=99, username="tester")
    return TestClient(app)


def test_get_experiment_dynamic_parameter_types():
    client = create_client()

    response = client.get("/api/laboratories/experiment-dynamic-parameter-types")

    assert response.status_code == 200
    assert response.json() == [
        {"name": "Drugs", "value": "Drugs"},
        {"name": "Strings", "value": "Strings"},
    ]
