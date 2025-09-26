# repositories/consultations_repository.py
from sqlalchemy.orm import Session
from typing import List, Optional

from dtos.auth import UserDTO
from dtos.consultation import ConsultationDTO, ConsultationCreate, ConsultationUpdate, ConsultationDetailDTO, \
    PresentingSymptomDTO
from models.consultation import Consultations, ClinicalExamination, ConsultationClinicalExamination, PresentingSymptom, \
    ConsultationRoS, ConsultationQueue, ConsultationPrescription
from models.lab.lab import QueueStatus
from models.transaction import Transaction
from repos.pharmacy.prescription_repository import PrescriptionRepository
from repos.services.service_cart_repository import ServiceCartRepository
from utils.functions import generate_transaction_id


class ConsultationsRepository:

    def __init__(self, db: Session):
        self.db = db
        self.service_cart_repository = ServiceCartRepository(db)

    def get(self, consultation_id: int) -> Optional[ConsultationDTO]:
        consultation = (
            self.db.query(Consultations)
            .filter(Consultations.id == consultation_id)
            .first()
        )
        return ConsultationDTO.from_orm(consultation) if consultation else None

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ConsultationDTO]:
        consultations = (
            self.db.query(Consultations)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [ConsultationDTO.from_orm(c) for c in consultations]

    def create(self, consultation_data_detail: ConsultationDetailDTO, created_by: UserDTO) -> ConsultationDTO:
        try:
            consultation_data = consultation_data_detail.consultation
            consultation_data.created_by = created_by.id
            consultation = Consultations(
                **consultation_data.dict(),
                # created_by=created_by
            )
            self.db.add(consultation)
            self.db.flush()

            # create transaction needed for clinical examinations
            transaction = Transaction(id=generate_transaction_id(), user_id=created_by.id, discount=0)

            self.db.add(transaction)
            self.db.flush()

            # create clinical examination if provided. use repository later
            clinical_examination_data = consultation_data_detail.clinical_examination
            clinical_examination_data.transaction_id = transaction.id
            ced = clinical_examination_data.dict()

            # exclude symptoms to avoid issues with serialization
            ced.pop('symptoms', None)
            cedr = ClinicalExamination(**ced)
            cedr.conducted_by = created_by.id
            self.db.add(cedr)
            self.db.flush()

            # link clinical examination to consultation
            self.db.add(ConsultationClinicalExamination(
                consultation_id=consultation.id,
                clinical_examination_id=cedr.id
            ))

            # add symptoms if any
            for symptom in clinical_examination_data.symptoms or []:
                symptom.clinical_examination_id = cedr.id
                self.db.add(
                    PresentingSymptom(**symptom.dict())
                )

            review_of_systems = consultation_data_detail.review_of_systems or []
            for ros in review_of_systems:
                ros.consultation_id = consultation.id
                if not ros.system or not ros.note:
                    continue
                self.db.add(ConsultationRoS(**ros.dict()))

            consultation_data_detail.client_service_cart.transaction_id = transaction.id
            consultation_data_detail.client_service_cart.created_by = created_by.id
            self.service_cart_repository.create_client_service_cart(
                consultation_data_detail.client_service_cart
            )

            # process prescription if any
            prescription = consultation_data_detail.prescription
            if prescription:
                prescription_repository = PrescriptionRepository(self.db)
                prescription_id = prescription_repository.create(prescription, created_by)
                if prescription_id:
                    # link prescription to consultation
                    self.db.add(
                        ConsultationPrescription(
                            consultation_id=consultation.id,
                            prescription_id=prescription_id.id
                        )
                    )

            # update consultation queue status to processed
            consultation_queue = self.db.query(ConsultationQueue).filter(
                ConsultationQueue.id == consultation_data.queue_id).first()
            if consultation_queue:
                consultation_queue.status = QueueStatus.Processed
                self.db.add(consultation_queue)

            self.db.commit()
            self.db.refresh(consultation)
            return ConsultationDTO.from_orm(consultation)
        except Exception as e:
            self.db.rollback()
            raise e

    def update(self, consultation_id: int, consultation_data: ConsultationUpdate) -> Optional[ConsultationDTO]:
        consultation = self.db.query(Consultations).filter(Consultations.id == consultation_id).first()
        if not consultation:
            return None
        for field, value in consultation_data.dict(exclude_unset=True).items():
            setattr(consultation, field, value)
        self.db.commit()
        self.db.refresh(consultation)
        return ConsultationDTO.from_orm(consultation)

    def delete(self, consultation_id: int) -> bool:
        consultation = self.db.query(Consultations).filter(Consultations.id == consultation_id).first()
        if not consultation:
            return False
        self.db.delete(consultation)
        self.db.commit()
        return True
