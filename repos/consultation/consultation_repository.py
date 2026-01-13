# repositories/consultations_repository.py
import json
from datetime import datetime, timedelta

from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from dtos.auth import UserDTO
from dtos.consultant import ConsultationDTO, ConsultationDetailDTO, ConsultationRoSDTO, ConsultationUpdate, \
    ConsultationQueueDTO
from dtos.consultation import PresentingSymptomDTO, ClinicalExaminationDTO, InHoursDTO, QuickConsultDTO
from dtos.pharmacy.prescription import PrescriptionDTO, PrescriptionDetailDTO
from dtos.service_dtos.client_cart_service import AppointmentData, ClientConsultationBookingCartDTO
from dtos.services import PriceCodeDTO, BusinessServiceDTO, ServiceBookingDTO, ServiceBookingDetailDTO
from models.consultation import Consultations, ClinicalExamination, ConsultationClinicalExamination, PresentingSymptom, \
    ConsultationRoS, ConsultationQueue, ConsultationPrescription, ConsultationHierarchy, InHours, ConsultationType
from models.lab.lab import QueueStatus
from models.pharmacy import Prescription, PrescriptionDetail
from models.services.service_cart import ClientConsultationBookingCart
from models.services.services import BookingType, ServiceBookingDetail, ServiceBooking, StoreVisibility, ServiceType
from models.transaction import Transaction
from repos.consultation.consultant_repository import ConsultantRepository
from repos.lab.lab_repository import LabRepository
from repos.pharmacy.prescription_repository import PrescriptionRepository
from repos.services.business_service_repository import BusinessServiceRepository
from repos.services.price_repository import PriceRepository
from repos.services.service_repository import ServiceRepository
from repos.services.service_cart_repository import ServiceCartRepository
from utils.functions import generate_transaction_id


class ConsultationsRepository:

    def __init__(self, db: Session):
        self.db = db
        self.consultant_repository = ConsultantRepository(db)  # Initialize your ConsultantRepository here if needed
        self.service_cart_repository = ServiceCartRepository(db)
        self.lab_repository = LabRepository(db)  # Initialize your LabRepository here if needed
        self.price_repository = PriceRepository(db)
        self.business_service_repository = BusinessServiceRepository(db)
        self.service_repository = ServiceRepository(db)

    def get(self, consultation_id: int) -> Optional[ConsultationDTO]:
        consultation = (
            self.db.query(Consultations)
            .filter(Consultations.id == consultation_id)
            .first()
        )
        return ConsultationDTO.from_orm(consultation) if consultation else None

    def get_consultation_details_by_queue_id(self, queue_id: int) -> ConsultationDetailDTO | None:
        # Fetch the consultation by queue_id
        consultation_obj = (
            self.db.query(Consultations)
            .filter(Consultations.queue_id == queue_id)
            .first()
        )
        if not consultation_obj:
            return None

        return self.get_consultation_details(consultation_obj)

    def get_consultation_details(self, consultation_obj: Consultations) -> ConsultationDetailDTO | None:
        # Fetch clinical examination (if any)
        clinical_exam_link = (
            self.db.query(ConsultationClinicalExamination)
            .filter(ConsultationClinicalExamination.consultation_id == consultation_obj.id)
            .first()
        )

        client_service_cart = None
        clinical_exam_dto = None
        if clinical_exam_link:
            clinical_exam_obj = (
                self.db.query(ClinicalExamination)
                .filter(ClinicalExamination.id == clinical_exam_link.clinical_examination_id)
                .first()
            )
            if clinical_exam_obj:
                clinical_exam_dto = ClinicalExaminationDTO.from_orm(clinical_exam_obj)
                client_service_cart = self.service_cart_repository.get_client_service_cart_by_transaction_id(
                    clinical_exam_obj.transaction_id
                )
                cart = []
                if client_service_cart:
                    for item in client_service_cart.client_service_cart_details or []:
                        if item.service_type == BookingType.Laboratory:
                            # get lab details by service_id
                            lab_details = self.lab_repository.get_lab_service_details_by_service_id(item.service_id)
                            item.service_desc = lab_details.lab_service_name
                            cart.append(item)
                        if item.service_type == BookingType.Appointment:
                            # get consultation booking details by service_id
                            item.service_desc = f"Appointment - Pending Desc"
                            item.appointment_data = item.client_consultation_booking_carts
                            cart.append(item)

                    client_service_cart.client_service_cart_details = cart
        # get prescription (if any)
        prescription_link = self.db.query(ConsultationPrescription) \
            .filter(ConsultationPrescription.consultation_cart_id == client_service_cart.id).one_or_none()
        prescription_dto = None

        if prescription_link:
            prescription_obj = self.db.query(Prescription) \
                .filter(Prescription.id == prescription_link.prescription_id).one_or_none()
            if prescription_obj:
                prescription_dto = PrescriptionDTO.from_orm(prescription_obj)
                # Fetch prescription details
                prescription_details = self.db.query(PrescriptionDetail) \
                    .filter(PrescriptionDetail.prescription_id == prescription_obj.id).all()
                prescription_dto.prescriptions = [PrescriptionDetailDTO.from_orm(detail) for detail in
                                                  prescription_details]

        # Fetch review of systems (if any)
        ros_objs = (
            self.db.query(ConsultationRoS)
            .filter(ConsultationRoS.consultation_id == consultation_obj.id)
            .all()
        )
        ros_dtos = [ConsultationRoSDTO.from_orm(ros) for ros in ros_objs] if ros_objs else []

        # You may need to fetch and construct client_service_cart and prescription as well, as in ConsultationDetailDTO
        # Here, set them to None or implement their retrieval if needed
        return ConsultationDetailDTO(
            consultation=ConsultationDTO.from_orm(consultation_obj),
            clinical_examination=clinical_exam_dto,
            review_of_systems=ros_dtos,
            client_service_cart=client_service_cart,
            prescription=prescription_dto
        )

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

    def create(self, cdd: ConsultationDetailDTO, created_by: UserDTO) -> ConsultationDTO:
        try:
            consultation_data = cdd.consultation

            # grab prescription early to avoid mutilation inside create_client_service_cart
            prescription_dto = (
                cdd.client_service_cart.prescription.model_copy(deep=True)
                if cdd.client_service_cart.prescription
                else None
            )

            # get consultant id by user id
            consultant = self.consultant_repository.get_consultant_by_user_id(created_by.id)
            if not consultant:
                raise ValueError(f"No consultant found for user ID: {created_by.id}")

            consultation = Consultations(
                consultation_type=cdd.consultation.consultation_type,
                created_by=consultant.id,
                queue_id=consultation_data.queue_id,
                reason_for_visit=consultation_data.reason_for_visit,
                preliminary_diagnosis=consultation_data.preliminary_diagnosis,
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
            clinical_examination_data = cdd.clinical_examination

            if clinical_examination_data:
                clinical_examination_dict = clinical_examination_data.dict()
                clinical_examination_dict["transaction_id"] = transaction.id

                clinical_examination_dict.pop("symptoms", None)

                cedr = ClinicalExamination(**clinical_examination_dict)
                cedr.conducted_by = created_by.id
                self.db.add(cedr)
                self.db.flush()

                self.db.add(
                    ConsultationClinicalExamination(
                        consultation_id=consultation.id,
                        clinical_examination_id=cedr.id
                    )
                )

                for symptom in clinical_examination_data.symptoms or []:
                    self.db.add(
                        PresentingSymptom(
                            symptom_id=symptom.symptom_id,
                            clinical_examination_id=cedr.id,
                            severity=symptom.severity,
                            frequency=symptom.frequency,
                            agreviating_factors=symptom.agreviating_factors
                        )
                    )

            review_of_systems = cdd.review_of_systems or []
            for ros in review_of_systems:
                ros.consultation_id = consultation.id
                if not ros.system or not ros.note:
                    continue
                self.db.add(ConsultationRoS(**ros.dict()))

            cdd.client_service_cart.transaction_id = transaction.id
            cdd.client_service_cart.created_by = created_by.id
            cart = self.service_cart_repository.create_client_service_cart(
                cdd.client_service_cart
            )

            # process prescription if any
            if prescription_dto:
                prescription_repository = PrescriptionRepository(self.db)
                prescription_id = prescription_repository.create(prescription_dto, created_by)
                if prescription_id:
                    # link prescription to consultation
                    self.db.add(
                        ConsultationPrescription(
                            consultation_cart_id=cart.id,
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

    def create_quick_consultation_queue(self, quick_consult: QuickConsultDTO) -> ConsultationQueueDTO:
        try:
            consultant = self.consultant_repository.get_consultant_by_id(quick_consult.consultant_id)
            if not consultant:
                raise ValueError(f"Consultant not found for ID: {quick_consult.consultant_id}")

            transaction = Transaction(
                id=generate_transaction_id(),
                user_id=consultant.user_id,
                discount=0
            )
            self.db.add(transaction)
            self.db.flush()

            price_code = self.price_repository.create(
                PriceCodeDTO(service_price=quick_consult.price, discount=0)
            )

            business_service = self.business_service_repository.create(
                BusinessServiceDTO(
                    price_code=price_code.id,
                    ext_turn_around_time=30,
                    visibility=StoreVisibility.Active,
                    service_type=ServiceType.Appointment
                )
            )

            service_booking = self.service_repository.create_service_booking(
                ServiceBookingDTO(client_id=quick_consult.client_id, transaction_id=transaction.id)
            )
            service_booking_id = service_booking["id"] if isinstance(service_booking, dict) else service_booking.id

            service_booking_detail = self.service_repository.create_service_booking_detail(
                ServiceBookingDetailDTO(
                    service_id=business_service.service_id,
                    price_code=price_code.id,
                    booking_id=service_booking_id,
                    booking_type=BookingType.Appointment
                )
            )
            service_booking_detail_id = (
                service_booking_detail["id"]
                if isinstance(service_booking_detail, dict)
                else service_booking_detail.id
            )

            start_time = datetime.utcnow()
            end_time = start_time + timedelta(minutes=30)
            in_hour = InHours(
                start_time=start_time,
                end_time=end_time,
                specialist_id=quick_consult.consultant_id,
                service_id=business_service.service_id
            )
            self.db.add(in_hour)
            self.db.flush()

            return self.consultant_repository.add_consultant_queue(
                ConsultationQueueDTO(
                    schedule_id=in_hour.id,
                    status=QueueStatus.Processing,
                    booking_id=service_booking_detail_id,
                    specialization_id=quick_consult.specialization_id,
                    notes=quick_consult.notes,
                    consultation_time=start_time
                )
            )
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

    def get_consultation_case_files(
            self,
            limit: int,
            skip: int,
            case_status: str,
            client_id: int = 0,
            consultation_type: ConsultationType = ConsultationType.base_case,
            ) -> List[ConsultationDTO]:

        query = (
            self.db.query(Consultations)
            .options(
                joinedload(Consultations.queue)
                .joinedload(ConsultationQueue.booking_detail)
                .joinedload(ServiceBookingDetail.booking),
                joinedload(Consultations.creator),
            )
            .order_by(Consultations.created_at.desc())
        )

        # Filter by consultation type
        if consultation_type:
            query = query.filter(Consultations.consultation_type == consultation_type)

        # Filter by case status
        if case_status:
            query = query.filter(Consultations.case_status == case_status)

        # Filter by client_id (through the booking chain)
        if client_id:
            query = (
                query.join(Consultations.queue)
                .join(ConsultationQueue.booking_detail)
                .join(ServiceBookingDetail.booking)
                .filter(ServiceBooking.client_id == client_id)
            )

        consultations = query.offset(skip).limit(limit).all()
        return consultations # [ConsultationDTO.from_orm(c) for c in consultations]

    def get_follow_up_consultation(self,
                                   consultation_id: int,
                                   skip: int = 0, limit: int = 100,
                                   case_status: str = 'Open') -> List[ConsultationDTO]:
        follow_ups = self.db.query(ConsultationHierarchy).filter(
            ConsultationHierarchy.base_consultation_id == consultation_id
        ).offset(skip).limit(limit).all()

        results = []
        for fu in follow_ups:
            consultation = self.db.query(Consultations).filter(
                Consultations.id == fu.follow_up_consultation_id
            ).first()
            if consultation:
                results.append(ConsultationDTO.from_orm(consultation))
        return results
