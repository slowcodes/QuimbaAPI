from pydantic import BaseModel
from typing import Optional


class LifestyleFactorDTO(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    value_type: str
    allowed_values: Optional[str] = None

    model_config = {"from_attributes": True}


class ClientLifestyleDTO(BaseModel):
    id: int
    patient_id: int
    factor_id: int
    value: Optional[str] = None
    factor: Optional[LifestyleFactorDTO] = None  # nested factor info

    class Config:
        from_attributes = True


