from sqlalchemy import Column, Boolean


class SoftDeleteMixin:
    is_deleted = Column(Boolean, default=False)

    def delete(self):
        self.is_deleted = True

    def restore(self):
        self.is_deleted = False

