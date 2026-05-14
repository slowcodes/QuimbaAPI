import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb")

from db import Base
from dtos.lab import ExpDTO, ExperimentDynamicParamTypeDTO, ExperimentParameterDTO
from models.lab.lab import (
    DynamicParameterType,
    Experiment,
    ExperimentDynamicParamType,
    ExperimentParameter,
    ParameterType,
)
from repos.lab.experiment_repository import ExperimentRepository


def create_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    return session


def test_update_experiment_creates_dynamic_parameter_type_only_experiment():
    session = create_session()
    repo = ExperimentRepository(session)

    repo.update_experiment(
        1,
        ExpDTO(
            description="Dynamic experiment",
            use_only_dynamic_param=True,
            dynamic_param_type=ExperimentDynamicParamTypeDTO(param_type=DynamicParameterType.Drugs),
            parameters=[
                ExperimentParameterDTO(
                    parameter="Ignored fixed parameter",
                    measuring_unit="mg",
                    parameter_type=ParameterType.Number,
                )
            ],
        ),
    )
    session.commit()

    experiment = session.query(Experiment).one()
    assert experiment.description == "Dynamic experiment"
    assert experiment.use_only_dynamic_param is True
    assert session.query(ExperimentParameter).count() == 0

    dynamic_param = session.query(ExperimentDynamicParamType).one()
    assert dynamic_param.experiment_id == experiment.id
    assert dynamic_param.param_type == DynamicParameterType.Drugs


def test_update_experiment_syncs_dynamic_parameter_types():
    session = create_session()
    repo = ExperimentRepository(session)
    experiment = Experiment(description="Existing", use_only_dynamic_param=True)
    session.add(experiment)
    session.flush()
    session.add(
        ExperimentDynamicParamType(
            experiment_id=experiment.id,
            param_type=DynamicParameterType.Drugs,
        )
    )
    session.commit()

    repo.update_experiment(
        1,
        ExpDTO(
            id=experiment.id,
            description="Updated",
            use_only_dynamic_param=True,
            dynamic_param_type=ExperimentDynamicParamTypeDTO(param_type=DynamicParameterType.Strings),
        ),
    )
    session.commit()

    session.refresh(experiment)
    assert experiment.description == "Updated"

    dynamic_params = session.query(ExperimentDynamicParamType).all()
    assert len(dynamic_params) == 1
    assert dynamic_params[0].param_type == DynamicParameterType.Strings
