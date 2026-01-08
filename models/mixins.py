from sqlalchemy import DateTime, Column, Boolean
import datetime


class SoftDeleteMixin:
    is_deleted = Column(Boolean, default=False)

    def delete(self):
        self.is_deleted = True

    def restore(self):
        self.is_deleted = False


class SoftDelMixin:
    deleted_at = Column(DateTime, default=None, nullable=True)

    def soft_delete(self):
        """Marks the record as deleted by setting the deleted_at timestamp."""
        self.deleted_at = datetime.datetime.utcnow()

    @classmethod
    def query(cls, session):
        """Override the query to exclude soft-deleted records by default."""
        return session.query(cls).filter(cls.deleted_at == None)

    def restore(self):
        """Restores a soft-deleted record by setting deleted_at to None."""
        self.deleted_at = None
