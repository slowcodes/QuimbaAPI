import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb")

from db import Base
from dtos.lab import DynamicParameterBaseDTO, LabResultByQueueDTO
from models.lab.lab import DynamicParameter, Experiment, ExperimentParameter, ExperimentResultReading, LabServicesQueue, \
    ParameterType, SampleResult
from repos.lab.queue_repository import QueueRepository
from repos.lab.result_repository import ResultRepository


def create_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    return session


def test_replace_dynamic_parameters_for_queue():
    session = create_session()
    repo = QueueRepository(session)
    experiment = Experiment(description="Dynamic experiment")
    queue = LabServicesQueue(lab_service_id=1, booking_id=1)
    session.add_all([experiment, queue])
    session.commit()

    result = repo.replace_dynamic_parameters(
        queue.id,
        [
            DynamicParameterBaseDTO(
                parameter="Drug",
                parameter_value="Ampicillin",
                exp_id=experiment.id,
            ),
            DynamicParameterBaseDTO(
                parameter="Sensitivity",
                parameter_value="Resistant",
                exp_id=experiment.id,
            ),
        ],
    )

    assert len(result) == 2
    assert result[0].lab_service_queue_id == queue.id
    assert result[0].parameter == "Drug"
    assert session.query(DynamicParameter).count() == 2

    replacement = repo.replace_dynamic_parameters(
        queue.id,
        [
            DynamicParameterBaseDTO(
                parameter="Drug",
                parameter_value="Ciprofloxacin",
                exp_id=experiment.id,
            )
        ],
    )

    assert len(replacement) == 1
    assert replacement[0].parameter_value == "Ciprofloxacin"
    assert session.query(DynamicParameter).count() == 1


def test_lab_result_by_queue_dto_includes_dynamic_parameters():
    session = create_session()
    experiment = Experiment(description="Dynamic experiment")
    queue = LabServicesQueue(lab_service_id=1, booking_id=1)
    session.add_all([experiment, queue])
    session.flush()
    session.add(SampleResult(queue_id=queue.id, created_by=1, comment="Ready"))
    session.add(
        DynamicParameter(
            lab_service_queue_id=queue.id,
            parameter="Drug",
            parameter_value="Ampicillin",
            exp_id=experiment.id,
        )
    )
    session.commit()
    session.refresh(queue)

    dto = LabResultByQueueDTO.from_orm(queue)

    assert dto.dynamic_parameters is not None
    assert len(dto.dynamic_parameters) == 1
    assert dto.dynamic_parameters[0].parameter == "Drug"
    assert dto.dynamic_parameters[0].parameter_value == "Ampicillin"
    assert dto.dynamic_parameters[0].experiment is not None
    assert dto.dynamic_parameters[0].experiment.description == "Dynamic experiment"
    assert dto.lab_result is not None
    assert dto.lab_result.experiment_readings is not None
    assert len(dto.lab_result.experiment_readings) == 1
    assert dto.lab_result.experiment_readings[0].experiment_id == experiment.id
    assert dto.lab_result.experiment_readings[0].parameters == []
    assert len(dto.lab_result.experiment_readings[0].dynamic_parameters) == 1
    assert dto.lab_result.experiment_readings[0].dynamic_parameters[0].parameter == "Drug"
    assert dto.lab_result.experiment_readings[0].dynamic_parameters[0].parameter_value == "Ampicillin"
    assert "dynamic_parameters" not in dto.lab_result.model_dump()


def test_lab_result_groups_experiment_readings_by_experiment():
    session = create_session()
    haematology = Experiment(description="Haematology")
    chemistry = Experiment(description="Chemistry")
    queue = LabServicesQueue(lab_service_id=1, booking_id=1)
    session.add_all([haematology, chemistry, queue])
    session.flush()

    haemoglobin = ExperimentParameter(
        parameter="Haemoglobin",
        measuring_unit="g/dL",
        parameter_type=ParameterType.Number,
        exp_id=haematology.id,
    )
    white_cells = ExperimentParameter(
        parameter="WBC",
        measuring_unit="10^9/L",
        parameter_type=ParameterType.Number,
        exp_id=haematology.id,
    )
    sodium = ExperimentParameter(
        parameter="Sodium",
        measuring_unit="mmol/L",
        parameter_type=ParameterType.Number,
        exp_id=chemistry.id,
    )
    session.add_all([haemoglobin, white_cells, sodium])
    session.flush()

    result = SampleResult(queue_id=queue.id, created_by=1, comment="Ready")
    session.add(result)
    session.flush()
    session.add_all(
        [
            ExperimentResultReading(
                result_id=result.id,
                parameter_id=haemoglobin.id,
                parameter_value="13.2",
            ),
            ExperimentResultReading(
                result_id=result.id,
                parameter_id=white_cells.id,
                parameter_value="5.5",
            ),
            ExperimentResultReading(
                result_id=result.id,
                parameter_id=sodium.id,
                parameter_value="139",
            ),
        ]
    )
    session.commit()
    session.refresh(queue)

    dto = LabResultByQueueDTO.from_orm(queue)

    assert dto.lab_result is not None
    assert dto.lab_result.experiment_readings is not None
    assert len(dto.lab_result.experiment_readings) == 2

    grouped = {
        experiment_reading.experiment_name: experiment_reading
        for experiment_reading in dto.lab_result.experiment_readings
    }
    assert len(grouped["Haematology"].parameters) == 2
    assert grouped["Haematology"].parameters[0].parameter.parameter == "Haemoglobin"
    assert grouped["Chemistry"].parameters[0].parameter.parameter == "Sodium"


def test_sample_results_include_dynamic_parameters_in_experiment_readings():
    session = create_session()
    repo = ResultRepository(session)
    experiment = Experiment(description="Culture")
    queue = LabServicesQueue(lab_service_id=1, booking_id=1)
    session.add_all([experiment, queue])
    session.flush()

    result = SampleResult(queue_id=queue.id, created_by=1, comment="Ready")
    session.add(result)
    session.add(
        DynamicParameter(
            lab_service_queue_id=queue.id,
            parameter="Drug",
            parameter_value="Ampicillin",
            exp_id=experiment.id,
        )
    )
    session.commit()

    response = repo.get_all_sample_results(limit=15, skip=0)
    dto = response["data"][0]

    assert dto.experiment_readings is not None
    assert len(dto.experiment_readings) == 1
    assert dto.experiment_readings[0].experiment_id == experiment.id
    assert dto.experiment_readings[0].parameters == []
    assert len(dto.experiment_readings[0].dynamic_parameters) == 1
    assert dto.experiment_readings[0].dynamic_parameters[0].parameter == "Drug"
    assert dto.experiment_readings[0].dynamic_parameters[0].parameter_value == "Ampicillin"
