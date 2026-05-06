from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from dtos.lab import (
    LabObservationResultTemplateCreateDTO,
    LabObservationResultTemplateDTO,
    LabObservationResultTemplateUpdateDTO,
)
from models.lab.lab import LabObservationResultTemplate


class LabObservationResultTemplateRepository:
    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    def _to_dto(template: LabObservationResultTemplate) -> LabObservationResultTemplateDTO:
        return LabObservationResultTemplateDTO.model_validate(template)

    def create_template(
        self,
        template: LabObservationResultTemplateCreateDTO,
        created_by: int,
    ) -> LabObservationResultTemplateDTO:
        db_template = LabObservationResultTemplate(
            **template.model_dump(exclude_unset=True),
            created_by=created_by,
        )
        self.session.add(db_template)
        self.session.commit()
        self.session.refresh(db_template)
        return self._to_dto(db_template)

    def get_template(self, template_id: int) -> Optional[LabObservationResultTemplateDTO]:
        template = (
            self.session.query(LabObservationResultTemplate)
            .filter(LabObservationResultTemplate.id == template_id)
            .first()
        )
        return self._to_dto(template) if template else None

    def get_templates(self, skip: int = 0, limit: int = 100, search_text: str = "") -> dict:
        query = self.session.query(LabObservationResultTemplate)

        if search_text:
            return self.search_templates(search_text=search_text, skip=skip, limit=limit)

        total = query.count()
        templates = (
            query.order_by(LabObservationResultTemplate.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return {
            "data": [self._to_dto(template) for template in templates],
            "total": total,
        }

    def search_templates(self, search_text: str, skip: int = 0, limit: int = 100) -> dict:
        query = self.session.query(LabObservationResultTemplate)

        if search_text:
            search_value = f"%{search_text}%"
            query = query.filter(
                or_(
                    LabObservationResultTemplate.template.ilike(search_value),
                    LabObservationResultTemplate.template_desc.ilike(search_value),
                )
            )

        total = query.count()
        templates = (
            query.order_by(LabObservationResultTemplate.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return {
            "data": [self._to_dto(template) for template in templates],
            "total": total,
        }

    def update_template(
        self,
        template_id: int,
        template_update: LabObservationResultTemplateUpdateDTO,
    ) -> Optional[LabObservationResultTemplateDTO]:
        template = (
            self.session.query(LabObservationResultTemplate)
            .filter(LabObservationResultTemplate.id == template_id)
            .first()
        )
        if not template:
            return None

        for key, value in template_update.model_dump(exclude_unset=True).items():
            setattr(template, key, value)

        self.session.commit()
        self.session.refresh(template)
        return self._to_dto(template)

    def delete_template(self, template_id: int) -> bool:
        template = (
            self.session.query(LabObservationResultTemplate)
            .filter(LabObservationResultTemplate.id == template_id)
            .first()
        )
        if not template:
            return False

        self.session.delete(template)
        self.session.commit()
        return True
