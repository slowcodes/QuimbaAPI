from typing import List, Optional

from sqlalchemy.orm import Session

from dtos.services import BusinessServiceDTO
from models.services.services import BusinessServices


class BusinessServiceRepository:
    def __init__(self, session: Session):
        self.db = session

    # Helper: Convert ORM → DTO
    @staticmethod
    def _to_dto(entity: BusinessServices) -> BusinessServiceDTO:
        return BusinessServiceDTO(
            service_id=entity.service_id,
            price_code=entity.price_code,
            ext_turn_around_time=entity.ext_turn_around_time,
            visibility=entity.visibility,
            service_type=entity.service_type
        )

    # Create
    def create(self, dto: BusinessServiceDTO) -> BusinessServiceDTO:
        service = BusinessServices(
            price_code=dto.price_code,
            ext_turn_around_time=dto.ext_turn_around_time,
            visibility=dto.visibility,
            service_type=dto.service_type
        )
        self.db.add(service)
        self.db.commit()
        self.db.refresh(service)
        return self._to_dto(service)

    # Get all
    def get_all(self) -> List[BusinessServiceDTO]:
        services = self.db.query(BusinessServices).all()
        return [self._to_dto(s) for s in services]

    # Get by ID
    def get_by_id(self, service_id: int) -> Optional[BusinessServiceDTO]:
        service = (
            self.db.query(BusinessServices)
            .filter(BusinessServices.service_id == service_id)
            .first()
        )
        return BusinessServiceDTO.from_orm(service) if service else None

    # Update
    def update(self, service_id: int, dto: BusinessServiceDTO) -> Optional[BusinessServiceDTO]:
        service = self.db.query(BusinessServices).filter(
            BusinessServices.service_id == service_id
        ).first()
        if not service:
            return None

        service.price_code = dto.price_code
        service.ext_turn_around_time = dto.ext_turn_around_time
        service.visibility = dto.visibility
        service.service_type = dto.service_type

        self.db.commit()
        self.db.refresh(service)
        return self._to_dto(service)

    # Delete
    def delete(self, service_id: int) -> bool:
        service = self.db.query(BusinessServices).filter(
            BusinessServices.service_id == service_id
        ).first()
        if not service:
            return False

        self.db.delete(service)
        self.db.commit()
        return True
