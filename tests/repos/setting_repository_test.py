import os
from unittest.mock import MagicMock

os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb")

from dtos.conf import ConfSettingDTO
from models.conf import ConfSetting, DataType, UIControlType
from repos.setting_repository import SettingRepository


def test_create_setting():
    mock_session = MagicMock()
    repo = SettingRepository(session=mock_session)

    input_dto = ConfSettingDTO(
        parameter="site_name",
        data_type=DataType.String,
        param_value="Quimba",
        ui_control_type=UIControlType.TextField,
    )

    def refresh_side_effect(obj):
        obj.id = 1

    mock_session.refresh.side_effect = refresh_side_effect

    result = repo.create_setting(input_dto)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()
    assert result.id == 1
    assert result.parameter == "site_name"
    assert result.ui_control_type == UIControlType.TextField


def test_get_setting_returns_none_when_missing():
    mock_session = MagicMock()
    repo = SettingRepository(session=mock_session)

    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = None
    mock_session.query.return_value = mock_query

    result = repo.get_setting(999)
    assert result is None


def test_update_setting_updates_fields():
    mock_session = MagicMock()
    repo = SettingRepository(session=mock_session)

    db_setting = ConfSetting(
        id=2,
        parameter="old_param",
        data_type=DataType.String,
        param_value="old",
        ui_control_type=UIControlType.TextField,
        is_deleted=False,
    )

    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = db_setting
    mock_session.query.return_value = mock_query

    update_dto = ConfSettingDTO(
        parameter="new_param",
        data_type=DataType.Text,
        param_value="new",
        ui_control_type=UIControlType.TextArea,
    )

    updated = repo.update_setting(2, update_dto)

    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(db_setting)
    assert updated is not None
    assert updated.parameter == "new_param"
    assert updated.data_type == DataType.Text
    assert updated.ui_control_type == UIControlType.TextArea


def test_delete_setting_marks_record_deleted():
    mock_session = MagicMock()
    repo = SettingRepository(session=mock_session)

    db_setting = ConfSetting(
        id=3,
        parameter="delete_me",
        data_type=DataType.String,
        param_value="x",
        ui_control_type=UIControlType.TextField,
        is_deleted=False,
    )

    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = db_setting
    mock_session.query.return_value = mock_query

    deleted = repo.delete_setting(3)

    assert deleted is True
    assert db_setting.is_deleted is True
    mock_session.commit.assert_called_once()
