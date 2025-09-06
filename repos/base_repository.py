# repositories/base.py

from sqlalchemy.orm import Session


class BaseRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, obj):
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get(self, model, obj_id):
        return self.db.query(model).filter(model.id == obj_id).first()

    def list(self, model):
        return self.db.query(model).all()

    def delete(self, obj):
        self.db.delete(obj)
        self.db.commit()

    def update(self):
        self.db.commit()
