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


class NotificationDTO(BaseModel):
    id: int
    title: str
    message: str
    user_id: int
    is_read: bool
    created_at: str