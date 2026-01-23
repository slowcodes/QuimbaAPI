from unittest.mock import MagicMock

from dtos.admission import BedCreateDTO, BedUpdateDTO, RoomCreateDTO, RoomUpdateDTO
from models.admission import Bed, BedRoomStatus, Rooms
from repos.admission.bed_repository import BedRepository
from repos.admission.room_repository import RoomRepository


def test_create_bed():
    mock_session = MagicMock()
    repo = BedRepository(session=mock_session)

    bed_input = BedCreateDTO(ward_id=1, bed_number="B-01", status=BedRoomStatus.Free)

    def commit_and_refresh(obj):
        obj.id = 1

    mock_session.add.side_effect = lambda x: None
    mock_session.commit.side_effect = lambda: None
    mock_session.refresh.side_effect = commit_and_refresh

    result = repo.create_bed(bed_input)

    mock_session.add.assert_called()
    mock_session.commit.assert_called()
    mock_session.refresh.assert_called()

    assert result.id == 1
    assert result.bed_number == "B-01"


def test_update_bed():
    mock_session = MagicMock()
    repo = BedRepository(session=mock_session)

    db_bed = Bed(id=1, ward_id=1, bed_number="B-01", status=BedRoomStatus.Free)
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = db_bed
    mock_session.query.return_value = mock_query

    update = BedUpdateDTO(bed_number="B-02")
    result = repo.update_bed(1, update)

    mock_session.commit.assert_called()
    mock_session.refresh.assert_called_with(db_bed)

    assert result.bed_number == "B-02"


def test_create_room():
    mock_session = MagicMock()
    repo = RoomRepository(session=mock_session)

    room_input = RoomCreateDTO(ward_id=1, room_number="R-01", capacity=2, description="Main")

    def commit_and_refresh(obj):
        obj.id = 1

    mock_session.add.side_effect = lambda x: None
    mock_session.commit.side_effect = lambda: None
    mock_session.refresh.side_effect = commit_and_refresh

    result = repo.create_room(room_input)

    mock_session.add.assert_called()
    mock_session.commit.assert_called()
    mock_session.refresh.assert_called()

    assert result.id == 1
    assert result.room_number == "R-01"


def test_update_room():
    mock_session = MagicMock()
    repo = RoomRepository(session=mock_session)

    db_room = Rooms(id=1, ward_id=1, room_number="R-01", capacity=2, description=None)
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = db_room
    mock_session.query.return_value = mock_query

    update = RoomUpdateDTO(room_number="R-02", capacity=3)
    result = repo.update_room(1, update)

    mock_session.commit.assert_called()
    mock_session.refresh.assert_called_with(db_room)

    assert result.room_number == "R-02"
    assert result.capacity == 3
