from datetime import datetime
from unittest.mock import MagicMock

from dtos.admission import AdmissionCreateDTO, AdmissionUpdateDTO
from models.admission import Admission
from repos.admission.admission_repository import AdmissionRepository


def test_create_admission():
    mock_session = MagicMock()
    repo = AdmissionRepository(session=mock_session)

    admission_input = AdmissionCreateDTO(
        bed_id=1,
        patient_id=2,
        admission_date=datetime.utcnow(),
        reason="Observation",
        user_id=3,
    )

    def commit_and_refresh(obj):
        obj.id = 1

    mock_session.add.side_effect = lambda x: None
    mock_session.commit.side_effect = lambda: None
    mock_session.refresh.side_effect = commit_and_refresh

    result = repo.create_admission(admission_input)

    mock_session.add.assert_called()
    mock_session.commit.assert_called()
    mock_session.refresh.assert_called()

    assert result.id == 1
    assert result.patient_id == 2


def test_update_admission():
    mock_session = MagicMock()
    repo = AdmissionRepository(session=mock_session)

    db_admission = Admission(
        id=1,
        bed_id=1,
        patient_id=2,
        admission_date=datetime.utcnow(),
        reason="Old",
        user_id=3,
    )
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = db_admission
    mock_session.query.return_value = mock_query

    update = AdmissionUpdateDTO(reason="Updated")
    result = repo.update_admission(1, update)

    mock_session.commit.assert_called()
    mock_session.refresh.assert_called_with(db_admission)

    assert result.reason == "Updated"
