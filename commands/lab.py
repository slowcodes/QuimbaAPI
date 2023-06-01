from typing import List

from pydantic import EmailStr, BaseModel
from datetime import datetime, date, time, timedelta

from models.lab import BoundaryType


class Laboratory(BaseModel):
    lab: str
    description: str


class LaboratoryGroup(BaseModel):
    group_name: str
    group_desc: str

class ParameterBounds(BaseModel):
    upper_bound: str
    lower_bound: str
    value_type: BoundaryType


class Parameter(BaseModel):
    parameter: str
    measuring_unit: str
    temp_exp_id: int
    bounds: List[ParameterBounds]


class Experiment(BaseModel):
    experiment: str
    temp_exp_id: int
    parameters: List[Parameter]


class BussServices(BaseModel):
    price_code: int


class LaboratoryService(BaseModel):
    groups: List[int]
    lab_id: int
    lab_service_name: str
    lab_service_desc: str
    experiment: List[Experiment]
    predefined_experiment_id: List[int]
    business_details: BussServices
