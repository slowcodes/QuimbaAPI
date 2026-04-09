import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb")

from db import Base
from models.lab.lab import Laboratory, LabService, LabType
from models.services.services import BusinessServices, PriceCode, ServiceType, StoreVisibility
from repos.lab.lab_repository import LabRepository


def create_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    return session


def seed_lab_service(session, *, lab_name: str, service_name: str, service_id: int):
    lab = Laboratory(lab_name=lab_name, lab_desc=f"{lab_name} description")
    session.add(lab)
    session.flush()

    price_code = PriceCode(service_price=100.0, discount=0.0)
    session.add(price_code)
    session.flush()

    business_service = BusinessServices(
        service_id=service_id,
        price_code=price_code.id,
        ext_turn_around_time=24,
        visibility=StoreVisibility.Active,
        service_type=ServiceType.Laboratory,
    )
    session.add(business_service)
    session.flush()

    session.add(
        LabService(
            lab_id=lab.id,
            lab_service_name=service_name,
            lab_service_desc=f"{service_name} description",
            lab_type=LabType.Experiment,
            service_id=business_service.service_id,
        )
    )
    session.commit()


def test_get_lab_services_search_by_lab_name_only_returns_matching_lab_services():
    session = create_session()
    repo = LabRepository(session)

    seed_lab_service(session, lab_name="Alpha Lab", service_name="Blood Test", service_id=1)
    seed_lab_service(session, lab_name="Beta Lab", service_name="Urine Test", service_id=2)

    result = repo.get_lab_services(skip=0, limit=10, lab_id=0, keyword="Alpha")

    assert result["total"] == 1
    assert len(result["data"]) == 1
    assert result["data"][0].lab_service_name == "Blood Test"
