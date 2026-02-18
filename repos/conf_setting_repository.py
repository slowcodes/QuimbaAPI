from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from dtos.conf import ConfSettingDTO
from models.conf import ConfSetting


class ConfSettingRepository:
    def __init__(self, db: Session):
        self.db = db

    # Utility: convert ORM -> DTO
    @staticmethod
    def _to_dto(entity: ConfSetting) -> ConfSettingDTO:
        return ConfSettingDTO(
            id=entity.id,
            parameter=entity.parameter,
            param_desc=entity.param_desc,
            data_type=entity.data_type,
            param_value=entity.param_value,
            ui_control_type=entity.ui_control_type
        )

    # Create
    def create(self, dto: ConfSettingDTO) -> ConfSettingDTO:
        setting = ConfSetting(
            parameter=dto.parameter,
            param_desc=dto.param_desc,
            data_type=dto.data_type,
            param_value=dto.param_value,
        )
        self.db.add(setting)
        self.db.commit()
        self.db.refresh(setting)
        return self._to_dto(setting)

    # Read all
    def get_all(self) -> List[ConfSettingDTO]:
        settings = (
            self.db.query(ConfSetting)
            .filter(
                or_(
                    ConfSetting.is_deleted == False,  # noqa: E712
                    ConfSetting.is_deleted.is_(None)
                )
            )
            .all()
        )
        return [self._to_dto(s) for s in settings]

    # Read one by ID
    def get_by_id(self, setting_id: int) -> Optional[ConfSettingDTO]:
        setting = (
            self.db.query(ConfSetting)
            .filter(ConfSetting.id == setting_id, ConfSetting.is_deleted == False)
            .first()
        )
        return self._to_dto(setting) if setting else None

    # Read one by parameter
    def get_by_parameter(self, parameter: str) -> Optional[ConfSettingDTO]:
        setting = (
            self.db.query(ConfSetting)
            .filter(ConfSetting.parameter == parameter, ConfSetting.is_deleted == False)
            .first()
        )
        return self._to_dto(setting) if setting else None

    # Update
    def update(self, setting_id: int, dto: ConfSettingDTO) -> Optional[ConfSettingDTO]:
        setting = (
            self.db.query(ConfSetting)
            .filter(ConfSetting.id == setting_id, ConfSetting.is_deleted == False)
            .first()
        )
        if not setting:
            return None

        setting.parameter = dto.parameter
        setting.param_desc = dto.param_desc
        setting.data_type = dto.data_type
        setting.param_value = dto.param_value

        self.db.commit()
        self.db.refresh(setting)
        return self._to_dto(setting)

    # Soft delete
    def delete(self, setting_id: int) -> bool:
        setting = (
            self.db.query(ConfSetting)
            .filter(ConfSetting.id == setting_id, ConfSetting.is_deleted == False)
            .first()
        )
        if not setting:
            return False

        setting.soft_delete()  # from SoftDeleteMixin
        self.db.commit()
        return True
