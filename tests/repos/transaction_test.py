from unittest.mock import MagicMock

from dtos.transaction import TransactionPackageDTO
from models.transaction import PackageTransaction
from repos.transaction_repository import TransactionRepository


def test_create_transaction_package():
    # Arrange
    mock_session = MagicMock()
    service = TransactionRepository(db_session=mock_session)

    dto_input = TransactionPackageDTO(transaction_id=98765432109, package_id=3)
    mock_model = PackageTransaction(id=1, transaction_id=98765432109, package_id=3)

    # Simulate what SQLAlchemy would do
    def commit_and_refresh(obj):
        obj.id = 1  # Simulate DB assigning an ID

    mock_session.add.side_effect = lambda x: None
    mock_session.commit.side_effect = lambda: None
    mock_session.refresh.side_effect = commit_and_refresh

    # Act
    result = service.create_transaction_package(dto_input)

    # Assert
    mock_session.add.assert_called()
    mock_session.commit.assert_called()
    mock_session.refresh.assert_called()

    assert isinstance(result, TransactionPackageDTO)
    assert result.id == 1
    assert result.transaction_id == 98765432109
    assert result.package_id == 3
