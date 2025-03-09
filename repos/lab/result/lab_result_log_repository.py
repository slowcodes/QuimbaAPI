from sqlalchemy.orm import Session

from commands.lab import LabResultLogCreate, LabResultLogUpdate
from models.lab.lab import LabResultLog, ResultStatus


class LabResultLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, log_id: int):
        return self.db.query(LabResultLog).filter(LabResultLog.id == log_id).first()

    def get_by_booking_id(self, booking_id: int, status_filter: ResultStatus):
        return self.db.query(LabResultLog).filter(LabResultLog.booking_id == booking_id, LabResultLog.action == status_filter).first()

    def get_all(self, skip: int = 0, limit: int = 10):
        return self.db.query(LabResultLog).offset(skip).limit(limit).all()

    def create(self, log_data: LabResultLogCreate):
        new_log = LabResultLog(**log_data.dict())
        self.db.add(new_log)
        self.db.commit()
        self.db.refresh(new_log)
        return new_log

    def update(self, log_id: int, log_data: LabResultLogUpdate):
        log = self.get_by_id(log_id)
        if not log:
            return None
        for key, value in log_data.dict(exclude_unset=True).items():
            setattr(log, key, value)
        self.db.commit()
        self.db.refresh(log)
        return log

    def delete_by_booking_id(self, log_id: int, resultStatus: ResultStatus):
        log = self.get_by_booking_id(log_id, resultStatus)
        if not log:
            return None
        self.db.delete(log)
        self.db.commit()
        return log
