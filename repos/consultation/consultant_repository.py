from datetime import timedelta, datetime
from typing import List, Optional

from sqlalchemy import and_, cast, DateTime
from sqlalchemy.orm import Session

from dtos.consultant import SpecialismDTO
from dtos.consultation import SymptomDTO, ClinicalExaminationDTO, PresentingSymptomDTO, ConsultantDTO, \
    InHoursDTO, ConsultationQueueDTO, ConsultationAppointmentDTO, BaseCaseDTO
from dtos.services import PriceCodeDTO
from models.consultation import Symptom, ClinicalExamination, PresentingSymptom, Specialist, Specialism, \
    SpecialistSpecialization, InHours, InHourFrequency, ConsultationQueue, InternalSystems, Consultations
from models.lab.lab import QueueStatus
from models.services.services import PriceCode, BusinessServices, StoreVisibility, ServiceType, ServiceBooking, \
    ServiceBookingDetail, BookingType
from models.transaction import Transaction
from repos.auth_repository import UserRepository
from repos.client.client_repository import ClientRepository
from repos.services.price_repository import PriceRepository
from repos.services.service_repository import ServiceRepository


class ConsultantRepository:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.service_repository = ServiceRepository(db)
        self.price_repository = PriceRepository(db)
        self.client_repository = ClientRepository(db)

        cols = [
            Transaction.transaction_time,
            Transaction.transaction_status,
            Specialist.id.label("specialist_id"),
            Transaction.id.label("transaction_id"),
            ConsultationQueue.id,
            ServiceBooking.client_id,
            ServiceBookingDetail.booking_id,
            ConsultationQueue.scheduled_at,
            ConsultationQueue.id.label("schedule_id"),
            ConsultationQueue.specialization_id.label("specialization_id"),
            ConsultationQueue.consultation_time,
            ConsultationQueue.notes,
            InHours.start_time,
            ConsultationQueue.status
        ]

        self.queue = self.db.query(*cols).select_from(ConsultationQueue) \
            .join(ServiceBookingDetail, ConsultationQueue.booking_id == ServiceBookingDetail.id) \
            .join(ServiceBooking, ServiceBooking.id == ServiceBookingDetail.booking_id) \
            .join(Transaction, Transaction.id == ServiceBooking.transaction_id) \
            .join(InHours, InHours.id == ConsultationQueue.schedule_id) \
            .join(Specialist, Specialist.id == InHours.specialist_id)

    def get_symptom(self) -> List[SymptomDTO]:
        symptoms = self.db.query(Symptom).all()
        return [SymptomDTO(symptom=symptom.symptom, id=symptom.id) for symptom in symptoms]

    def in_hours_dto(self, hours: InHours) -> InHoursDTO:
        return InHoursDTO(
            id=hours.id,
            start_time=hours.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            end_time=hours.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            specialist_id=hours.specialist_id,
            frequency=hours.frequency,
            business_service=self.service_repository.get_business_service_by_id(hours.service_id)
        )

    def addInHours(self, in_hours: InHoursDTO) -> InHoursDTO:
        price = self.price_repository.create(
            PriceCodeDTO(
                service_price=in_hours.business_service.price_code.service_price,
                discount=in_hours.business_service.price_code.discount
            )
        )

        # This is also a service. Therefore list as a service
        business_service = BusinessServices(
            price_code=price.id,
            ext_turn_around_time=in_hours.business_service.ext_turn_around_time,
            visibility=StoreVisibility.Active,
            serviceType=ServiceType.Consultation
        )
        self.db.add(business_service)
        self.db.flush()

        hours = InHours(
            start_time=in_hours.start_time,
            end_time=in_hours.end_time,
            specialist_id=in_hours.specialist_id,
            frequency=in_hours.frequency,
            service_id=business_service.service_id
        )
        self.db.add(hours)
        self.db.commit()
        self.db.refresh(hours)
        return self.in_hours_dto(hours)

    def get_expanded_in_hours(self, start_date: str, end_date: str, consultant_id: int) -> List[InHoursDTO]:
        days: List[InHoursDTO] = []

        current = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        end = current + timedelta(days=6)

        # Validate that start_time is before or equal to end_time
        if current > end:
            print("Error: start_time is after end_time. No schedule to expand.")
            return days

        while current <= end:

            in_hour_schedule = self.db.query(InHours).filter(
                and_(
                    InHours.start_time <= current,
                    InHours.end_time <= end
                )).all()

            for ih in in_hour_schedule:
                st_time = ih.start_time.time()
                ed_time = ih.end_time.time()

                weekday = current.weekday()  # 0 = Monday, 6 = Sunday
                add = False

                if ih.frequency == InHourFrequency.Daily:
                    add = True
                elif ih.frequency == InHourFrequency.Weekly:
                    add = current.weekday() == ih.start_time.weekday()
                elif ih.frequency == InHourFrequency.EveryDayOfTheWeek:
                    add = True
                elif ih.frequency == InHourFrequency.EveryWeekDay:
                    add = weekday < 5

                if add:
                    slot = InHoursDTO(
                        id=ih.id,
                        specialist_id=ih.specialist_id,
                        business_service=self.service_repository.get_business_service_by_id(ih.service_id),
                        frequency=ih.frequency.value,
                        start_time=current.strftime("%Y-%m-%d") + " " + str(st_time),
                        end_time=current.strftime("%Y-%m-%d") + " " + str(ed_time),
                    )
                    days.append(slot)

            current += timedelta(days=1)

        return days

    def add_consultant_queue(self, consultant_queue: ConsultationQueueDTO):
        try:
            obj = ConsultationQueue(
                schedule_id=consultant_queue.schedule_id,
                # scheduled_at=consultant_queue.scheduled_at,
                status=consultant_queue.status,
                booking_id=consultant_queue.booking_id,
                specialization_id=consultant_queue.specialization_id,
                notes=consultant_queue.notes,
                consultation_time=consultant_queue.consultation_time
            )
            self.db.add(obj)
            self.db.commit()
            self.db.refresh(obj)
            res = ConsultationQueueDTO(
                id=obj.id,
                schedule_id=obj.schedule_id,
                # scheduled_at=consultant_queue.scheduled_at.strftime("%Y-%m-%d"),
                # consultation_time=consultant_queue.consultation_time.strftime("%Y-%m-%d %H:%M:%S"),
                status=obj.status,
                booking_id=obj.booking_id,
                specialization_id=obj.specialization_id,
                notes=obj.notes
            )

            return res
        except Exception as e:
            self.db.rollback()
            print(f"Error adding consultant queue: {e}")

    def get_consultant_queue(
            self,
            consultant_id: int = 0,
            client_id: int = 0,
            start_date: Optional[str] = None,
            last_date: Optional[str] = None,
            in_hour_id: int = 0,
            status: Optional[str] = None
    ) -> List[ConsultationAppointmentDTO]:
        query = self.queue

        # Apply consultant filter
        if consultant_id:
            query = query.filter(Specialist.id == consultant_id)

        # Apply in-hour filter
        if in_hour_id:
            query = query.filter(InHours.id == in_hour_id)

        # Apply client filter
        if client_id:
            query = query.filter(ServiceBooking.client_id == client_id)

        # Apply status filter
        if status:
            query = query.filter(ConsultationQueue.status == status)

        # Helper to safely convert to datetime
        def to_datetime(value):
            if isinstance(value, datetime):
                return value
            if isinstance(value, str) and value.strip():
                try:
                    # Handles ISO formats like "2025-09-28" or "2025-09-28T12:30:00"
                    return datetime.fromisoformat(value)
                except ValueError:
                    try:
                        # Fallback to simple date
                        return datetime.strptime(value, "%Y-%m-%d")
                    except ValueError:
                        raise ValueError(f"Invalid date format: {value}")
            return None

        # Apply date range filter
        start_dt = to_datetime(start_date + " 00:00:00") if start_date else None
        last_dt = to_datetime(last_date + " 23:59:59") if last_date else None

        if start_dt and last_dt:
            query = query.filter(and_(
                ConsultationQueue.scheduled_at >= start_dt,
                ConsultationQueue.scheduled_at <= last_dt
            ))

        # Execute the query
        res = query.all()

        # Process results
        bookings = []
        for booking in res:
            bookings.append(
                ConsultationAppointmentDTO(
                    specialist=self.get_consultant(booking.specialist_id),
                    client=self.client_repository.get_client(booking.client_id),
                    time_of_appointment=booking.consultation_time.strftime("%Y-%m-%d %H:%M:%S"),
                    date_of_appointment=booking.start_time.strftime("%Y-%m-%d"),
                    booking_id=booking.booking_id,
                    transaction_id=booking.transaction_id,
                    scheduled_at=booking.scheduled_at.strftime("%Y-%m-%d %H:%M:%S"),
                    status=booking.status,
                    id=booking.id
                )
            )

        return bookings

    def get_consultation_service_booking(self, transaction_id: int):
        cols = [
            ServiceBooking.id.label("booking_id"),
            ServiceBookingDetail.price_code,
            ServiceBookingDetail.id.label("booking_detail_id"),
            ServiceBookingDetail.service_id,
            ServiceBookingDetail.booking_type,
            InHours.specialist_id,
            Specialism.department,
            ServiceBooking.client_id,
            PriceCode.service_price,
            PriceCode.id.label("service_price_code"),
            BusinessServices.ext_turn_around_time,
            ServiceBooking.transaction_id,
        ]

        app_res = self.db.query(*cols).select_from(ServiceBookingDetail). \
            join(ServiceBooking, ServiceBooking.id == ServiceBookingDetail.booking_id). \
            join(PriceCode, PriceCode.id == ServiceBookingDetail.price_code). \
            join(ConsultationQueue, ConsultationQueue.booking_id == ServiceBookingDetail.id). \
            join(InHours, InHours.id == ConsultationQueue.schedule_id). \
            join(Specialism, Specialism.id == ConsultationQueue.specialization_id). \
            join(BusinessServices, BusinessServices.service_id == InHours.service_id). \
            filter(ServiceBookingDetail.booking_type == BookingType.Appointment)

        res = app_res.filter(ServiceBooking.transaction_id == transaction_id).all()

        cos = []
        for result in res:
            consultant = self.get_consultant(result.specialist_id)
            service_desc = result.department + " Consultation with " + consultant.user.first_name + " " + consultant.user.last_name
            cos.append({
                'booking_details_id': result.booking_detail_id,
                'service_id': result.service_id,
                'lab_service_name': service_desc,
                # 'lab_service_desc': result.lab_service_desc,
                'price_code': result.service_price_code,
                'price': result.service_price,
                'ext_turn_around_time': result.ext_turn_around_time
            })
        return cos

    def get_clinical_examination(db: Session, clinical_examination_id: int) -> ClinicalExaminationDTO:
        db_clinical_examination = db.query(ClinicalExamination).filter(
            ClinicalExamination.id == clinical_examination_id).first()
        return ClinicalExaminationDTO(**db_clinical_examination.__dict__) if db_clinical_examination else None

    def update_clinical_examination(db: Session, db_clinical_examination: ClinicalExamination,
                                    clinical_examination_data: ClinicalExaminationDTO) -> ClinicalExaminationDTO:
        for field, value in clinical_examination_data.dict().items():
            setattr(db_clinical_examination, field, value)
        db.commit()
        db.refresh(db_clinical_examination)
        return ClinicalExaminationDTO(**db_clinical_examination.__dict__)

    def create_presenting_symptom(db: Session, presenting_symptom_data: PresentingSymptomDTO) -> PresentingSymptomDTO:
        db_presenting_symptom = PresentingSymptom(**presenting_symptom_data.dict())
        db.add(db_presenting_symptom)
        db.commit()
        db.refresh(db_presenting_symptom)
        return PresentingSymptomDTO(**db_presenting_symptom.__dict__)

    def get_presenting_symptom(db: Session, presenting_symptom_id: int) -> PresentingSymptomDTO:
        db_presenting_symptom = db.query(PresentingSymptom).filter(
            PresentingSymptom.id == presenting_symptom_id).first()
        return PresentingSymptomDTO(**db_presenting_symptom.__dict__) if db_presenting_symptom else None

    def update_presenting_symptom(db: Session, db_presenting_symptom: PresentingSymptom,
                                  presenting_symptom_data: PresentingSymptomDTO) -> PresentingSymptomDTO:
        for field, value in presenting_symptom_data.dict().items():
            setattr(db_presenting_symptom, field, value)
        db.commit()
        db.refresh(db_presenting_symptom)
        return PresentingSymptomDTO(**db_presenting_symptom.__dict__)

    # PresentingSymptom Repository
    def create_presenting_symptom(db: Session, presenting_symptom: PresentingSymptomDTO) -> ClinicalExaminationDTO:
        db_presenting_symptom = PresentingSymptom(**presenting_symptom.dict())
        db.add(db_presenting_symptom)
        db.commit()
        db.refresh(db_presenting_symptom)
        return {
            'id': db_presenting_symptom.id,
            'severity': db_presenting_symptom.severity,
            'frequency': db_presenting_symptom.frequency,
            'symptom_id': db_presenting_symptom.symptom_id,
            'clinical_examination_id': db_presenting_symptom.clinical_examination_id
        }

    # ClinicalExamination Repository
    def create_clinical_examination(self, clinical_examination: ClinicalExaminationDTO) -> ClinicalExaminationDTO:
        # db_clinical_examination = ClinicalExamination(**clinical_examination.dict())
        db_clinical_examination = ClinicalExamination(
            presenting_complaints=clinical_examination.presenting_complaints,
            transaction_id=clinical_examination.transaction_id,
            conducted_by=1
        )
        self.db.add(db_clinical_examination)
        self.db.commit()
        self.db.refresh(db_clinical_examination)

        sym: List[PresentingSymptomDTO] = []
        for symp in clinical_examination.symptoms:
            sym.append(
                self.create_presenting_symptom(
                    PresentingSymptomDTO(
                        symptom_id=symp.symptom_id,
                        clinical_examination_id=db_clinical_examination.id,
                        severity=symp.severity,
                        frequency=symp.frequency
                    )
                )
            )

        return {
            'id': db_clinical_examination.id,
            'transaction_id': db_clinical_examination.transaction_id,
            'conducted_by': db_clinical_examination.conducted_by,
            'symptoms': sym,
            'conducted_at': db_clinical_examination.conducted_at,
            'presenting_complaints': db_clinical_examination.presenting_complaints
        }

    def get_clinical_examination(self, clinical_examination_id: int) -> Optional[ClinicalExamination]:
        return self.db.query(ClinicalExamination).filter(ClinicalExamination.id == clinical_examination_id).first()

    def update_clinical_examination(self, clinical_examination_id: int,
                                    clinical_examination: ClinicalExaminationDTO) -> Optional[ClinicalExaminationDTO]:
        db_clinical_examination = self.db.query(ClinicalExamination).filter(
            ClinicalExamination.id == clinical_examination_id).first()
        if db_clinical_examination:
            update_data = clinical_examination.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_clinical_examination, key, value)
            self.db.commit()
            self.db.refresh(db_clinical_examination)
        return db_clinical_examination

    def delete_clinical_examination(self, clinical_examination_id: int) -> Optional[ClinicalExaminationDTO]:
        db_clinical_examination = self.db.query(ClinicalExamination).filter(
            ClinicalExamination.id == clinical_examination_id).first()
        if db_clinical_examination:
            self.db.delete(db_clinical_examination)
            self.db.commit()
        return db_clinical_examination

    def get_consultant_by_user_id(self, user_id: int):
        return self.db.query(Specialist).filter(Specialist.user_id == user_id).first()

    def get_consultant_by_id(self, consultant_id: int):
        return self.db.query(Specialist).filter(Specialist.id == consultant_id).first()

    def get_specializations(self, limit: int = 100, skip: int = 0):
        return self.db.query(Specialism).limit(limit).offset(skip).all()

    def add_consultant_specialization(self, consultant_id: int, specialization_id):
        consultant = self.get_consultant_by_id(consultant_id)
        if consultant:
            spec = SpecialistSpecialization(specialist_id=consultant.id, specialism_id=specialization_id)
            self.db.add(spec)
            self.db.commit()
            self.db.refresh(spec)
            return spec
        return None

    def add_consultant(self, consultant_dto: ConsultantDTO):
        consultant = Specialist(
            user_id=consultant_dto.user.id,
            title=consultant_dto.title
        )

        try:
            self.db.add(consultant)
            self.db.commit()
            self.db.refresh(consultant)

            for specialization in consultant_dto.specializations:
                self.add_consultant_specialization(consultant.id, specialization.id)

            return ConsultantDTO(
                id=consultant.id,
                user=consultant_dto.user,
                title=consultant.title,
                specializations=consultant_dto.specializations
            )
        except Exception as e:
            self.db.rollback()
            raise e

    def update_consultant(self, consultant_id: int, consultant_dto: ConsultantDTO):
        consultant = self.get_consultant_by_id(consultant_id)
        if consultant:
            consultant.title = consultant_dto.title
            self.db.commit()
            self.db.refresh(consultant)

            # Update specializations
            existing_specializations = self.db.query(SpecialistSpecialization).filter(
                SpecialistSpecialization.specialist_id == consultant.id).all()
            existing_spec_ids = {spec.specialism_id for spec in existing_specializations}
            new_spec_ids = {spec.id for spec in consultant_dto.specializations}

            # Add new specializations
            for spec_id in new_spec_ids - existing_spec_ids:
                self.add_consultant_specialization(consultant.id, spec_id)

            # Remove old specializations
            for spec in existing_specializations:
                if spec.specialism_id not in new_spec_ids:
                    self.db.delete(spec)
            self.db.commit()

            return ConsultantDTO(
                id=consultant.id,
                user=consultant_dto.user,
                title=consultant.title,
                specializations=consultant_dto.specializations
            )
        return None

    def get_consultants(self, skip: int = 0, limit: int = 100) -> List[ConsultantDTO]:

        query = self.db.query(Specialist).offset(skip).limit(limit).all()
        consultants = []
        for consultant in query:
            specializations = self.db.query(Specialism).join(SpecialistSpecialization,
                                                             Specialism.id == SpecialistSpecialization.specialism_id).filter(
                SpecialistSpecialization.specialist_id == consultant.id).all()

            consultants.append(
                ConsultantDTO(
                    id=consultant.id,
                    user=self.user_repository.get_usr_by_id(consultant.user_id),
                    title=consultant.title,
                    specializations=[
                        SpecialismDTO(id=spec.id, department=spec.department, specialist_title=spec.specialist_title)
                        for spec in specializations]
                )
            )
        return consultants

    def get_consultation_queue_by_id(self, queue_id: int):
        qu = self.queue.filter(ConsultationQueue.id == queue_id).first()
        booking_details = self.get_consultation_service_booking(qu.transaction_id)[0]
        client = self.client_repository.get_client(qu.client_id)
        return ConsultationQueueDTO(
            id=qu.id,
            schedule_id=qu.schedule_id,
            scheduled_at=qu.scheduled_at.strftime("%Y-%m-%d %H:%M:%S"),
            consultation_time=qu.consultation_time.strftime("%Y-%m-%d %H:%M:%S"),
            status=qu.status,
            booking_detail=booking_details,
            client=client,
            booking_id=qu.booking_id,
            specialization_id=qu.specialization_id,
            notes=qu.notes,
            base_cases=self.get_base_cases_by_client_id(client["id"])
        )

    def get_base_cases_by_client_id(self, client_id: int) -> List[BaseCaseDTO]:
        base_cases = []
        cols = [
            Consultations.id,
            Consultations.reason_for_visit,
            Consultations.preliminary_diagnosis,
            Consultations.created_at,
            Consultations.case_status
        ]
        queue = self.db.query(*cols).select_from(Consultations) \
            .join(ConsultationQueue, ConsultationQueue.id == Consultations.queue_id) \
            .join(ServiceBookingDetail, ConsultationQueue.booking_id == ServiceBookingDetail.id) \
            .join(ServiceBooking, ServiceBooking.id == ServiceBookingDetail.booking_id) \
            .filter(ServiceBooking.client_id == client_id).all()

        for q in queue:
            base_cases.append(
                BaseCaseDTO(
                    consultation_id=q.id,
                    presenting_complaint=q.reason_for_visit,
                    preliminary_diagnosis=q.preliminary_diagnosis,
                    date_of_visit=q.created_at,
                    case_status=q.case_status
                )
            )
        return base_cases

    def get_consultant(self, consultant_id: int):
        consultant = self.db.query(Specialist).filter(Specialist.id == consultant_id).one_or_none()

        if consultant:
            specializations = self.db.query(Specialism) \
                .join(SpecialistSpecialization, Specialism.id == SpecialistSpecialization.specialism_id) \
                .filter(SpecialistSpecialization.specialist_id == consultant_id).all()
            return ConsultantDTO(
                id=consultant.id,
                user=self.user_repository.get_usr_by_id(consultant.user_id),
                title=consultant.title,
                specializations=[
                    SpecialismDTO(id=spec.id, department=spec.department, specialist_title=spec.specialist_title)
                    for spec in specializations]
            )

    def get_internal_systems(self) -> List[str]:
        # get enum internal systems
        return [e.value for e in InternalSystems]
