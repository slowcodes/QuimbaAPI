import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb")

from db import Base
from decimal import Decimal

from dtos.lab import ExperimentDynamicParamTypeDTO, ExpDTO, LaboratoryServiceDetailDTO
from models.lab.lab import DynamicParameterType, Experiment, ExperimentDynamicParamType, Laboratory, LabService, LabType
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


def test_add_lab_services_persists_dynamic_experiment_configuration():
    session = create_session()
    repo = LabRepository(session)
    lab = Laboratory(lab_name="Dynamic Lab", lab_desc="Dynamic Lab description")
    session.add(lab)
    session.commit()

    created = repo.add_lab_services(
        LaboratoryServiceDetailDTO(
            groups=[],
            name="Drug Sensitivity",
            description="Dynamic drug sensitivity panel",
            exps=[
                ExpDTO(
                    description="Sensitivity",
                    use_only_dynamic_param=True,
                    dynamic_param_type=ExperimentDynamicParamTypeDTO(param_type=DynamicParameterType.Drugs),
                )
            ],
            lab_type=LabType.Experiment,
            price=Decimal("100.00"),
            discount=Decimal("0.00"),
            visibility=StoreVisibility.Active,
            lab_id=lab.id,
            est_turn_around_time=24,
        )
    )

    assert created is True
    experiment = session.query(Experiment).one()
    assert experiment.use_only_dynamic_param is True

    dynamic_param = session.query(ExperimentDynamicParamType).one()
    assert dynamic_param.experiment_id == experiment.id
    assert dynamic_param.param_type == DynamicParameterType.Drugs
