from typing import List, TypeVar, Generic

from pydantic import BaseModel


class StatusDTO(BaseModel):
    parent: int
    children: List[int]
    status: str


T = TypeVar("T")


class DataResponseDTO(BaseModel, Generic[T]):
    data: List[T]
    total: int


class EnumItem(BaseModel):
    key: str
    value: str
