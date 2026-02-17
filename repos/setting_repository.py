from typing import List, Optional

from sqlalchemy.orm import Session

from dtos.conf import ConfSettingDTO
from models.conf import ConfSetting


class SettingRepository:
    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    def _to_dto(setting: ConfSetting) -> ConfSettingDTO:
        return ConfSettingDTO(
            id=setting.id,
            parameter=setting.parameter,
            data_type=setting.data_type,
            param_value=setting.param_value,
            ui_control_type=setting.ui_control_type,
        )

    def create_setting(self, setting: ConfSettingDTO) -> ConfSettingDTO:
        db_setting = ConfSetting(
            parameter=setting.parameter,
            data_type=setting.data_type,
            param_value=setting.param_value,
            ui_control_type=setting.ui_control_type,
        )
        self.session.add(db_setting)
        self.session.commit()
        self.session.refresh(db_setting)
        return self._to_dto(db_setting)

    def get_settings(self, skip: int = 0, limit: int = 100) -> List[ConfSettingDTO]:
        records = (
            self.session.query(ConfSetting)
            .filter(ConfSetting.is_deleted.is_(False))
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [self._to_dto(record) for record in records]

    def get_setting(self, setting_id: int) -> Optional[ConfSettingDTO]:
        record = (
            self.session.query(ConfSetting)
            .filter(ConfSetting.id == setting_id, ConfSetting.is_deleted.is_(False))
            .first()
        )
        return self._to_dto(record) if record else None

    def update_setting(self, setting_id: int, setting: ConfSettingDTO) -> Optional[ConfSettingDTO]:
        record = (
            self.session.query(ConfSetting)
            .filter(ConfSetting.id == setting_id, ConfSetting.is_deleted.is_(False))
            .first()
        )
        if not record:
            return None

        record.parameter = setting.parameter
        record.data_type = setting.data_type
        record.param_value = setting.param_value
        record.ui_control_type = setting.ui_control_type
        self.session.commit()
        self.session.refresh(record)
        return self._to_dto(record)

    def delete_setting(self, setting_id: int) -> bool:
        record = (
            self.session.query(ConfSetting)
            .filter(ConfSetting.id == setting_id, ConfSetting.is_deleted.is_(False))
            .first()
        )
        if not record:
            return False

        record.is_deleted = True
        self.session.commit()
        return True
