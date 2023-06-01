from sqlalchemy.orm import Session

from commands.lab import Laboratory, LaboratoryGroup, LaboratoryService
from models.client import *
from models.lab import Laboratories, LabServiceGroup, LabServices


def get_all_labs(db: Session, skip, limit):
    return db.query(Laboratories).offset(skip).limit(limit).all()


def get_all_labs_groups(db: Session, skip, limit):
    return db.query(LabServiceGroup).offset(skip).limit(limit).all()


def get_all_lab_services(db: Session, skip, limit, lab_id: int):
    return db.query(LabServices). \
        join(Laboratories, LabServices.lab_id == lab_id). \
        offset(skip).limit(limit).all()


def add_lab_services(db: Session, laboratoryService: LaboratoryService):
    return laboratoryService.lab_service_desc


def add_lab(db: Session, lab: Laboratory) -> Boolean:
    counter = db.query(Laboratories).where(Laboratories.lab_name == lab.lab).count()
    if counter <= 0:
        new_lab = Laboratories(
            lab_name=lab.lab,
            lab_desc=lab.description
        )
        db.add(new_lab)
        db.commit()
        db.refresh(new_lab)
        return True

    return False


def add_lab_group(db: Session, grp: LaboratoryGroup) -> Boolean:
    counter = db.query(LabServiceGroup).where(LabServiceGroup.group_name == grp.group_name).count()
    if counter <= 0:
        new_grp = LabServiceGroup(group_name=grp.group_name, group_desc=grp.group_desc)
        db.add(new_grp)
        db.commit()
        db.refresh(new_grp)
        return True

    return False
