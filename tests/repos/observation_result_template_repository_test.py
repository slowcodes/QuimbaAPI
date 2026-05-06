import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb")

from db import Base
from dtos.lab import (
    LabObservationResultTemplateCreateDTO,
    LabObservationResultTemplateUpdateDTO,
)
from models.auth import User
from repos.lab.observation_result_template_repository import (
    LabObservationResultTemplateRepository,
)


def create_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    return session


def test_create_template_sets_created_by_and_created_at():
    session = create_session()
    session.add(User(id=42, username="lab-user"))
    session.commit()
    repo = LabObservationResultTemplateRepository(session)

    result = repo.create_template(
        LabObservationResultTemplateCreateDTO(
            template="Observation text",
            template_desc="General observation",
        ),
        created_by=42,
    )

    assert result.id is not None
    assert result.template == "Observation text"
    assert result.template_desc == "General observation"
    assert result.created_by == 42
    assert result.created_at is not None
    assert result.user.username == "lab-user"


def test_search_templates_matches_template_and_description():
    session = create_session()
    repo = LabObservationResultTemplateRepository(session)

    repo.create_template(
        LabObservationResultTemplateCreateDTO(
            template="Normal chest observation",
            template_desc="Radiology",
        ),
        created_by=1,
    )
    repo.create_template(
        LabObservationResultTemplateCreateDTO(
            template="Unrelated",
            template_desc="Cardiology observation",
        ),
        created_by=1,
    )
    repo.create_template(
        LabObservationResultTemplateCreateDTO(
            template="Blood result",
            template_desc="Haematology",
        ),
        created_by=1,
    )

    result = repo.search_templates(search_text="observation", skip=0, limit=10)

    assert result["total"] == 2
    assert {item.template_desc for item in result["data"]} == {
        "Radiology",
        "Cardiology observation",
    }


def test_update_and_delete_template():
    session = create_session()
    repo = LabObservationResultTemplateRepository(session)
    created = repo.create_template(
        LabObservationResultTemplateCreateDTO(
            template="Original",
            template_desc="Original desc",
        ),
        created_by=7,
    )

    updated = repo.update_template(
        created.id,
        LabObservationResultTemplateUpdateDTO(template_desc="Updated desc"),
    )

    assert updated.template == "Original"
    assert updated.template_desc == "Updated desc"
    assert repo.delete_template(created.id) is True
    assert repo.get_template(created.id) is None
