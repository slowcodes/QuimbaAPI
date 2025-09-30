# repositories/consultations_repository.py
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from dtos.auth import UserDTO
from dtos.consultation import ConsultationDTO, ConsultationCreate, ConsultationUpdate, ConsultationDetailDTO, \
    PresentingSymptomDTO, ClinicalExaminationDTO, ConsultationRoSDTO
from dtos.pharmacy.prescription import PrescriptionDTO, PrescriptionDetailDTO
from models.consultation import Consultations, ClinicalExamination, ConsultationClinicalExamination, PresentingSymptom, \
    ConsultationRoS, ConsultationQueue, ConsultationPrescription, ConsultationHierarchy
from models.lab.lab import QueueStatus
from models.pharmacy import Prescription
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

    def get_all(self, skip: int = 0, limit: int = 100, client_id: int = 0) -> List[ConsultationDetailDTO]:
        query = (
            self.db.query(Consultations)
            .options(
                joinedload(Consultations.queue),
                joinedload(Consultations.creator),
                joinedload(Consultations.consultation_clinical_examinations)
                .joinedload(ConsultationClinicalExamination.clinical_examination)
                .joinedload(ClinicalExamination.symptoms),
                joinedload(Consultations.consultation_prescriptions)
                .joinedload(ConsultationPrescription.prescription)
                .joinedload(Prescription.details),  # make sure this matches your model
                joinedload(Consultations.review_of_systems),
            )
            .offset(skip)
            .limit(limit)
        )

        if client_id:
            query = query.join(Consultations.queue).filter(ConsultationQueue.client_id == client_id)

        consultations = query.all()
        result = []
        for c in consultations:
            # Clinical Examination (first one if any)
            clinical_examination = None
            clinical_examinations = [
                ccx.clinical_examination for ccx in getattr(c, "consultation_clinical_examinations", [])
                if ccx.clinical_examination
            ]
            if clinical_examinations:
                ce = clinical_examinations[0]
                symptoms = [PresentingSymptomDTO.from_orm(symptom) for symptom in getattr(ce, "symptoms", [])]
                clinical_examination = ClinicalExaminationDTO(
                    id=ce.id,
                    presenting_complaints=ce.presenting_complaints,
                    conducted_at=ce.conducted_at,
                    conducted_by=ce.conducted_by,
                    symptoms=symptoms,
                    transaction_id=ce.transaction_id,
                )

            # Prescription (first one if any, with items)
            prescription = None
            prescriptions = [
                cp.prescription for cp in getattr(c, "consultation_prescriptions", [])
                if cp.prescription
            ]
            if prescriptions:
                pres = prescriptions[0]
                items = [PrescriptionDetailDTO.from_orm(item) for item in getattr(pres, "items", [])]
                prescription = PrescriptionDTO(
                    # fill in other prescription fields as needed
                    id=pres.id,
                    issued_by=pres.issued_by,
                    issued_at=pres.issued_at,
                    items=items,
                    # ... add other fields from your PrescriptionDTO as needed
                )

            # Review of Systems
            review_of_systems = [
                ConsultationRoSDTO.from_orm(ros)
                for ros in getattr(c, "review_of_systems", [])
            ]

            detail = ConsultationDetailDTO(
                consultation=ConsultationDTO.from_orm(c),
                clinical_examination=clinical_examination,
                prescription=prescription,
                review_of_systems=review_of_systems,
            )
            result.append(detail)
        return result

    def create(self, consultation_data_detail: ConsultationDetailDTO, created_by: UserDTO) -> ConsultationDTO:
        try:
            consultation_data = consultation_data_detail.consultation
            consultation_data.created_by = created_by.id

            # remove base_case_id from consultation_to match the Consultations model
            cons_data = consultation_data.dict()
            cons_data.pop('base_case_id', None)

            print(cons_data)
            consultation = Consultations(
                **cons_data
            )
            self.db.add(consultation)
            self.db.flush()

            if consultation_data.base_case_id:
                # record hierarchy
                self.db.add(
                    ConsultationHierarchy(
                        base_consultation_id=consultation_data.base_case_id,
                        follow_up_consultation_id=consultation.id
                    )
                )

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
