from typing import Any, Dict, List, Optional, TypeVar, Generic

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
    description: Optional[str] = None
    message: List[Dict[str, Any]]
    user_id: int
    is_read: bool
    created_at: str
