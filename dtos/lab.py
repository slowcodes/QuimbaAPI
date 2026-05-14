from typing import List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from decimal import Decimal

from dtos.auth import BasicUserDTO
from dtos.services import ServiceBookingDetailDTO, BusinessServiceDTO, PriceCodeDTO
from models.lab.lab import BoundaryType, QueueStatus, QueuePriority, SampleType, ResultStatus, ParameterType, LabType, \
    DynamicParameterType
from models.services.services import StoreVisibility, ServiceType


class LaboratoryDTO(BaseModel):
    id: Optional[int] = None
    lab_name: str
    lab_desc: str = None

    class Config:
        from_attributes = True


class LaboratoryGroupDTO(BaseModel):
    group_name: str
    group_desc: str

    class Config:
        from_attributes = True


class LabServiceGroupTagDTO(BaseModel):
    id: Optional[int] = None
    lab_service_group: int
    lab_service_id: int
    group: Optional[LaboratoryGroupDTO] = None

    class Config:
        from_attributes = True


class ParameterBoundaryDTO(BaseModel):
    upper_bound: str
    lower_bound: str
    boundary_type: BoundaryType
    boundary_id: Optional[Decimal] = None

    class Config:
        from_attributes = True


class ExperimentParameterDTO(BaseModel):
    id: Union[int, float, str] = None
    parameter: str
    measuring_unit: str
    parameter_type: ParameterType
    exp_id: Optional[int] = None
    stacking_order: int = 0
    boundary: List[ParameterBoundaryDTO] = []

    class Config:
        from_attributes = True


class ExperimentDynamicParamTypeDTO(BaseModel):
    id: Optional[int] = None
    experiment_id: Optional[int] = None
    param_type: DynamicParameterType

    class Config:
        from_attributes = True


class ExpDTO(BaseModel):
    id: Optional[int] = None
    description: str = None
    use_only_dynamic_param: bool = False
    parameters: List[ExperimentParameterDTO] = []
    dynamic_param_type: Optional[ExperimentDynamicParamTypeDTO] = None

    class Config:
        from_attributes = True


class LabServiceExperimentDTO(BaseModel):
    id: Optional[int] = None
    lab_service_id: int
    experiment_id: Optional[int] = None

    experiment: Optional[ExpDTO]

    class Config:
        from_attributes = True


class LabServiceDTO(BaseModel):
    id: Optional[int] = None
    lab_id: Optional[int] = None
    lab_service_name: Optional[str] = None
    lab_service_desc: Optional[str] = None
    service_id: Optional[int] = None
    lab_type: LabType

    business_service: Optional[BusinessServiceDTO] = None
    lab_experiments: List[LabServiceExperimentDTO] = []
    laboratory: Optional[LaboratoryDTO] = None
    lab_service_group_tag: List[LabServiceGroupTagDTO] = []

    class Config:
        from_attributes = True


class LabObservationResultTemplateBaseDTO(BaseModel):
    template: Optional[str] = None
    template_desc: Optional[str] = None

    class Config:
        from_attributes = True


class LabObservationResultTemplateCreateDTO(LabObservationResultTemplateBaseDTO):
    pass


class LabObservationResultTemplateUpdateDTO(BaseModel):
    template: Optional[str] = None
    template_desc: Optional[str] = None

    class Config:
        from_attributes = True


class LabObservationResultTemplateDTO(LabObservationResultTemplateBaseDTO):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None
    user: Optional[BasicUserDTO] = None


class LaboratoryServiceDetailDTO(BaseModel):
    lab_service_id: Optional[int] = None
    groups: List[int]
    name: str
    description: str
    exps: List[ExpDTO]
    lab_type: LabType
    price: Decimal
    discount: Decimal
    visibility: StoreVisibility
    lab_id: int
    est_turn_around_time: int


class LabServicesQueueCreateDTO(BaseModel):
    lab_service_id: int
    booking_id: int


class DynamicParameterBaseDTO(BaseModel):
    parameter: str
    parameter_value: Optional[str] = None
    exp_id: int

    class Config:
        from_attributes = True


class DynamicParameterCreateDTO(DynamicParameterBaseDTO):
    lab_service_queue_id: int


class DynamicParameterUpdateDTO(BaseModel):
    parameter: Optional[str] = None
    parameter_value: Optional[str] = None
    exp_id: Optional[int] = None

    class Config:
        from_attributes = True


class DynamicParameterDTO(DynamicParameterBaseDTO):
    id: Optional[int] = None
    lab_service_queue_id: int
    experiment: Optional[ExpDTO] = Field(default=None, validation_alias="lab_experiment")

    class Config:
        from_attributes = True


class LabServiceQueueBase(BaseModel):
    id: Optional[int] = None
    lab_service_id: int
    scheduled_at: Optional[datetime] = None  # Default is None if not provided
    status: Optional[QueueStatus] = QueueStatus.Processing  # Default is None if not provided
    priority: Optional[QueuePriority] = QueuePriority.Normal
    booking_id: int

    booking: Optional[ServiceBookingDetailDTO] = []
    lab_service: Optional[LabServiceDTO] = None

    class Config:
        from_attributes = True


class CollectedSamplesBaseDTO(BaseModel):
    id: Optional[int] = None
    queue_id: int
    sample_type: SampleType
    collected_by: int
    collected_at: Optional[datetime] = None
    status: Optional[QueueStatus] = QueueStatus.Processing
    container_label: str

    class Config:
        from_attributes = True


class CollectedSamplesCreateDTO(BaseModel):
    id: Optional[int] = None
    queue_id: int
    sample_type: SampleType
    collected_by: int
    status: Optional[QueueStatus] = QueueStatus.Processing
    container_label: str

    class Config:
        from_attributes = True


class ExperimentResultReadingDTO(BaseModel):
    id: Optional[int] = None
    parameter_id: int
    parameter_value: str
    result_id: int
    created_at: Optional[datetime] = None

    parameter: Optional[ExperimentParameterDTO] = None

    class Config:
        from_attributes = True


class ExperimentResultReadingParameterDTO(BaseModel):
    id: Optional[int] = None
    parameter_id: int
    parameter_value: str
    result_id: int
    created_at: Optional[datetime] = None

    parameter: Optional[ExperimentParameterDTO] = None

    class Config:
        from_attributes = True


class ExperimentReadingsDTO(BaseModel):
    experiment_id: Optional[int] = None
    experiment_name: Optional[str] = None
    experiment: Optional[ExpDTO] = None
    parameters: List[ExperimentResultReadingParameterDTO] = []
    dynamic_parameters: List[DynamicParameterDTO] = Field(default_factory=list)

    class Config:
        from_attributes = True


class VerifiedResultEntryDTO(BaseModel):
    id: Optional[int] = None
    result_id: int
    verified_at: Optional[datetime] = None
    verified_by: Optional[int] = None
    comment: Optional[str] = None
    status: Optional[str] = None

    user: Optional[BasicUserDTO] = None

    class Config:
        from_attributes = True


class SampleResultDTO(BaseModel):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    queue_id: int
    created_by: int
    comment: str
    status: Optional[ResultStatus] = ResultStatus.Ready

    experiment_readings: Optional[List[ExperimentReadingsDTO]] = None
    dynamic_parameters: Optional[List[DynamicParameterDTO]] = Field(default=None, exclude=True)
    user: Optional[BasicUserDTO] = None
    verification: Optional[VerifiedResultEntryDTO] = None
    queue: Optional[LabServiceQueueBase] = None

    class Config:
        from_attributes = True

    @field_validator("experiment_readings", mode="before")
    @classmethod
    def group_experiment_readings(cls, readings):
        if not readings:
            return readings

        if isinstance(readings, list) and readings and isinstance(readings[0], dict) and "parameters" in readings[0]:
            return readings

        grouped = {}
        for reading in readings:
            parameter = cls._get_attr(reading, "parameter")
            experiment = cls._get_attr(parameter, "lab_experiment") if parameter is not None else None
            experiment_id = cls._get_attr(parameter, "exp_id")
            experiment_name = cls._get_attr(experiment, "description") if experiment is not None else None
            group_key = experiment_id if experiment_id is not None else f"unknown-{len(grouped)}"

            if group_key not in grouped:
                grouped[group_key] = {
                    "experiment_id": experiment_id,
                    "experiment_name": experiment_name,
                    "experiment": experiment,
                    "parameters": [],
                }

            grouped[group_key]["parameters"].append(
                {
                    "id": cls._get_attr(reading, "id"),
                    "parameter_id": cls._get_attr(reading, "parameter_id"),
                    "parameter_value": cls._get_attr(reading, "parameter_value"),
                    "result_id": cls._get_attr(reading, "result_id"),
                    "created_at": cls._get_attr(reading, "created_at"),
                    "parameter": parameter,
                }
            )

        return list(grouped.values())

    @model_validator(mode="after")
    def attach_dynamic_parameters_to_experiment_readings(self):
        if not self.dynamic_parameters:
            return self

        experiment_readings = list(self.experiment_readings or [])
        for experiment_reading in experiment_readings:
            experiment_reading.dynamic_parameters = []

        readings_by_experiment = {
            experiment_reading.experiment_id: experiment_reading
            for experiment_reading in experiment_readings
        }

        for dynamic_parameter in self.dynamic_parameters:
            experiment_id = dynamic_parameter.exp_id
            experiment_reading = readings_by_experiment.get(experiment_id)
            if experiment_reading is None:
                experiment = dynamic_parameter.experiment
                experiment_reading = ExperimentReadingsDTO(
                    experiment_id=experiment_id,
                    experiment_name=experiment.description if experiment else None,
                    experiment=experiment,
                    parameters=[],
                    dynamic_parameters=[],
                )
                experiment_readings.append(experiment_reading)
                readings_by_experiment[experiment_id] = experiment_reading

            experiment_reading.dynamic_parameters.append(dynamic_parameter)

        self.experiment_readings = experiment_readings
        return self

    @staticmethod
    def _get_attr(value, name):
        if value is None:
            return None
        if isinstance(value, dict):
            return value.get(name)
        return getattr(value, name, None)


class LabServicesQueueDTO(LabServiceQueueBase):
    lab_result: Optional[SampleResultDTO] = None
    samples: Optional[List[CollectedSamplesBaseDTO]] = None
    dynamic_parameters: Optional[List[DynamicParameterDTO]] = None

    class Config:
        from_attributes = True


class CollectedSamplesDTO(CollectedSamplesBaseDTO):
    user: Optional[BasicUserDTO] = None
    queue: Optional[LabServicesQueueDTO] = None

    collected_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LabResultByQueueDTO(LabServiceQueueBase):
    sample: Optional[CollectedSamplesDTO] = None
    lab_result: Optional[SampleResultDTO] = None
    dynamic_parameters: Optional[List[DynamicParameterDTO]] = None


    class Config:
        from_attributes = True


class DateFilterDTO(BaseModel):
    start_date: Optional[datetime] = None
    last_date: Optional[datetime] = None
    status: Optional[str]


class LabBusinessServiceDTO(BaseModel):
    service_id: Optional[int] = None
    price_code: Optional[int] = None
    pc: Optional[PriceCodeDTO] = None
    ext_turn_around_time: float
    visibility: Optional[StoreVisibility]
    service_type: Optional[ServiceType]

    lab_service: Optional[LabServiceDTO] = None

    class Config:
        from_attributes = True


class LabBundleCollectionDTO(BaseModel):
    id: Optional[int] = None
    bundles_id: Optional[int] = None
    lab_service_id: Optional[int] = None

    lab_service: Optional[LabServiceDTO] = None

    class Config:
        from_attributes = True


class LabServiceBundleDTO(BaseModel):
    id: Optional[int] = None
    bundles_name: Optional[str] = None
    bundles_desc: Optional[str] = None
    discount: float
    bundle_type: ServiceType
    collections: List[LabBundleCollectionDTO]

    class Config:
        from_attributes = True


class ApprovedLabBookingResultDTO(BaseModel):
    id: Optional[int] = None
    booking_id: int
    approved_at: Optional[datetime] = None
    approved_by: Optional[int] = None
    comment: Optional[str] = None
    status: str

    user: Optional[BasicUserDTO] = None

    class Config:
        from_attributes = True


class LabResultLogBase(BaseModel):
    booking_id: int
    logged_by: int
    action: ResultStatus


class LabResultLogCreate(LabResultLogBase):
    pass  # No extra fields required when creating a new log


class LabResultLogUpdate(BaseModel):
    action: Optional[ResultStatus]  # Only allow updating the action field
