from typing import Optional, List

from pydantic import BaseModel

from dtos.lab import LabBundleCollectionDTO
from models.services.services import ServiceType


class BundleDTO(BaseModel):
    id: Optional[int] = None
    bundles_name: Optional[str] = None
    bundles_desc: Optional[str] = None
    discount: float
    bundle_type: Optional[ServiceType] = None

    lab_service_bundle: Optional[List[LabBundleCollectionDTO]] = []

    class Config:
        from_attributes = True