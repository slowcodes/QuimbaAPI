from pydantic import BaseModel
from typing import Optional


class Icd10DTO(BaseModel):
    id: int
    url: Optional[str]
    head_code: str
    name: str

    class Config:
        from_attributes = True


class Icd10Create(BaseModel):
    url: Optional[str] = None
    head_code: str
    name: str


class Icd10Update(BaseModel):
    url: Optional[str] = None
    head_code: Optional[str] = None
    name: Optional[str] = None


class Icd10Response(BaseModel):
    total: int
    data: list[Icd10DTO]
