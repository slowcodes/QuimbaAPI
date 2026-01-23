from unittest.mock import MagicMock

from dtos.admission import WardCreateDTO, WardUpdateDTO
from models.admission import Ward, WardType
from repos.admission.ward_repository import WardRepository


def test_create_ward():
    mock_session = MagicMock()
    repo = WardRepository(session=mock_session)

    ward_input = WardCreateDTO(name="Ward A", description="Primary ward", ward_type=WardType.General)

    def commit_and_refresh(obj):
        obj.id = 1

    mock_session.add.side_effect = lambda x: None
    mock_session.commit.side_effect = lambda: None
    mock_session.refresh.side_effect = commit_and_refresh

    result = repo.create_ward(ward_input)

    mock_session.add.assert_called()
    mock_session.commit.assert_called()
    mock_session.refresh.assert_called()

    assert result.id == 1
    assert result.name == "Ward A"
    assert result.ward_type == WardType.General


def test_update_ward():
    mock_session = MagicMock()
    repo = WardRepository(session=mock_session)

    db_ward = Ward(id=1, name="Old Ward", description=None, ward_type=WardType.General)
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = db_ward
    mock_session.query.return_value = mock_query

    update = WardUpdateDTO(name="Updated Ward", description="Updated")
    result = repo.update_ward(1, update)

    mock_session.commit.assert_called()
    mock_session.refresh.assert_called_with(db_ward)

    assert result.name == "Updated Ward"
    assert result.description == "Updated"
