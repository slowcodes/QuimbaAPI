from datetime import date, datetime
from typing import List, Optional
import logging

from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Session

from dtos.services import ServiceBookingDTO, ServiceBookingDetailDTO, BusinessServiceDTO, ServiceBookingWithTrxDTO
from models.client import Client, Person
from models.lab.lab import CollectedSamples, LabBundleCollection, LabService, LabServicesQueue, QueueStatus, LabType
from models.services.services import Bundles, ServiceBooking, ServiceBookingDetail, BookingStatus, \
    ServiceClinicalExamination, BusinessServices, BookingType
from models.transaction import Transaction
from repos.services.price_repository import PriceRepository


class ServiceRepository:
    def __init__(self, session: Session):
        self.session = session
        self.price_repository = PriceRepository(session)

    def get_discounted_packages(self, service_id):
        cols = [
            Bundles.bundles_name,
            Bundles.bundles_desc,
            Bundles.discount,
            LabBundleCollection.bundles_id,
            LabBundleCollection.lab_service_id
        ]

        rs = self.session.query(*cols).select_from(LabBundleCollection) \
            .join(Bundles) \
            .filter(LabBundleCollection.lab_service_id == service_id).all()

        collections = []
        for bundle in rs:
            collections.append(
                {
                    'bundles_name': bundle.bundles_name,
                    'bundles_desc': bundle.bundles_desc,
                    'discount': bundle.discount,
                    'bundles_id': bundle.bundles_id,
                    'service_id': bundle.lab_service_id
                }
            )
        return collections

    def create_service_booking(self, service_booking: ServiceBookingDTO) -> ServiceBookingDTO:
        # db_service_booking = ServiceBooking(**service_booking.dict())
        db_service_booking = ServiceBooking(
            client_id=service_booking.client_id,
            transaction_id=service_booking.transaction_id
        )
        self.session.add(db_service_booking)
        self.session.commit()
        self.session.refresh(db_service_booking)

        return self.service_booking_to_DTO(db_service_booking)

    def create_service_booking_detail(self, service_booking: ServiceBookingDetailDTO) -> ServiceBookingDetailDTO:
        db_service_booking_details = ServiceBookingDetail(
            service_id=service_booking.service_id,
            price_code=service_booking.price_code,
            booking_id=service_booking.booking_id,
            booking_type=service_booking.booking_type
        )

        self.session.add(db_service_booking_details)
        self.session.commit()
        self.session.refresh(db_service_booking_details)

        return self.service_booking_detail_to_DTO(db_service_booking_details)

    def service_booking_to_DTO(self, sb: ServiceBooking) -> ServiceBookingDTO:
        return {
            'id': sb.id,
            'client_id': sb.client_id,
            'transaction_id': sb.transaction_id,
        }

    def service_booking_detail_to_DTO(self, sb: ServiceBookingDetail) -> ServiceBookingDTO:
        return {
            'id': sb.id,
            'service_id': sb.service_id,
            'price_code': sb.price_code,
            'booking_id': sb.booking_id,
        }

    def get_service_booking(self, booking_id: int) -> ServiceBookingDTO:
        return self.session.query(ServiceBooking).filter(ServiceBooking.id == booking_id).first()

    @staticmethod
    def _parse_date_filter_value(value):
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
            except ValueError:
                return value
        return value

    def get_all_service_bookings(
        self,
        limit: int,
        skip: int,
        client_id: int = 0,
        start_date: Optional[str] = None,
        last_date: Optional[str] = None,
        status: Optional[str] = None,
        booking_type: Optional[str] = None,
        lab_id: Optional[int] = None,
        search_text: Optional[str] = None,
    ) -> dict:

        query = self.session.query(ServiceBooking)
        joined_transaction = False
        joined_booking_detail = False
        joined_client = False
        joined_person = False
        needs_distinct = False

        if client_id != 0:
            query = query.filter(ServiceBooking.client_id == client_id)

        start_date = self._parse_date_filter_value(start_date)
        last_date = self._parse_date_filter_value(last_date)
        if start_date or last_date:
            query = query.join(Transaction, Transaction.id == ServiceBooking.transaction_id)
            joined_transaction = True
            if start_date and last_date:
                query = query.filter(Transaction.transaction_date.between(start_date, last_date))
            elif start_date:
                query = query.filter(Transaction.transaction_date >= start_date)
            else:
                query = query.filter(Transaction.transaction_date <= last_date)

        if booking_type == BookingType.Laboratory:
            # get transactions that have laboratory service bookings
            query = query.join(ServiceBookingDetail).filter(
                ServiceBookingDetail.booking_type == BookingType.Laboratory
            )
            joined_booking_detail = True
            needs_distinct = True

        if lab_id:
            if not joined_booking_detail:
                query = query.join(ServiceBookingDetail)
                joined_booking_detail = True
            query = query.join(LabServicesQueue, LabServicesQueue.booking_id == ServiceBookingDetail.id) \
                .join(LabService, LabService.id == LabServicesQueue.lab_service_id) \
                .filter(LabService.lab_id == lab_id)
            needs_distinct = True

        search_text = (search_text or "").strip()
        if search_text:
            keyword = f"%{search_text}%"
            if not joined_transaction:
                query = query.join(Transaction, Transaction.id == ServiceBooking.transaction_id)
                joined_transaction = True
            if not joined_client:
                query = query.join(Client, Client.id == ServiceBooking.client_id)
                joined_client = True
            if not joined_person:
                query = query.join(Person, Person.id == Client.person_id)
                joined_person = True
            query = query.filter(
                or_(
                    Person.first_name.ilike(keyword),
                    Person.last_name.ilike(keyword),
                    Person.middle_name.ilike(keyword),
                    cast(ServiceBooking.id, String).ilike(keyword),
                    cast(ServiceBooking.transaction_id, String).ilike(keyword),
                    cast(Transaction.id, String).ilike(keyword),
                )
            )


        if status:
            try:
                booking_status = BookingStatus(status)
                query = query.filter(ServiceBooking.booking_status == booking_status)
            except ValueError:
                pass
        if needs_distinct:
            query = query.distinct()

        total = query.order_by(None).count()
        selected_booking = query.order_by(ServiceBooking.id.desc()).offset(skip).limit(limit).all()

        data = [ServiceBookingWithTrxDTO.from_orm(booking) for booking in selected_booking]

        return {
            'data': data,
            'total': total
        }

    def get_booking_details_by_booking_id(self, booking_id: int) -> List[ServiceBookingDetailDTO]:
        sv_bks = self.session.query(ServiceBookingDetail).filter(ServiceBookingDetail.booking_id == booking_id).all()

        response = []
        for sv_bk in sv_bks:
            response.append(
                self.service_booking_detail_to_DTO(sv_bk)
            )

        return response

    def get_booking_details_by_booking_id(self, booking_id: int) -> List[ServiceBookingDetailDTO]:
        booking_detail = self.session.query(ServiceBookingDetail).filter(ServiceBookingDetail.booking_id == booking_id).all()
        return [ServiceBookingDetailDTO.from_orm(detail) for detail in booking_detail]

    def update_service_booking(self, service_booking: ServiceBookingDTO,
                               new_service_booking: ServiceBooking) -> ServiceBookingDTO:
        for var, value in vars(new_service_booking).items():
            setattr(service_booking, var, value) if value else None
        self.session.commit()
        self.session.refresh(service_booking)
        return service_booking

    def delete_service_booking(self, service_booking: ServiceBookingDTO) -> None:
        self.session.delete(service_booking)
        self.session.commit()

    def delete_service_booking_by_id(self, service_booking: ServiceBooking) -> dict:
        """
        Delete a ServiceBooking by its ID.

        :param service_booking:
        :param db: Database session
        :param service_booking_id: ID of the ServiceBooking to delete
        :return: True if deletion was successful, False otherwise
        """
        # service_booking = self.session.query(ServiceBooking).filter(ServiceBooking.id == service_booking.id).first()
        if service_booking:
            delete_booking = self.delete_service_booking_details_by_booking_id(service_booking)

            if delete_booking['delete']:
                self.session.delete(service_booking)

                # Delete transaction if it has no service booking
                self.session.query(ServiceClinicalExamination).filter(ServiceClinicalExamination.booking_id == service_booking.id).delete()
                self.session.commit()

            return delete_booking
        return {
            'msg': 'Service booking not found',
            'delete': False
        }

    def delete_service_booking_details_by_booking_id(self, service_booking: ServiceBooking) -> dict:
        try:

            booking_details = self.session.query(ServiceBookingDetail).filter(ServiceBookingDetail.booking_id == service_booking.id).all()
            if not booking_details:
                # No booking details found for the given booking ID. Howerver, we can still delete the booking
                return {
                    'msg': f'No booking details found for the given booking ID {service_booking.id}',
                    'delete': True
                }

            if service_booking.booking_type == 'Laboratory':
                for bk_details in booking_details:
                    # Check if a queue exists for the booking detail
                    queue = self.session.query(LabServicesQueue).filter(
                        LabServicesQueue.booking_id == bk_details.id
                    ).first()
                    if queue:
                        # Check if samples exist for the queue
                        samples_exist = (
                                self.session.query(CollectedSamples)
                                .filter(CollectedSamples.queue_id == queue.id)
                                .first() is not None
                        )
                        if samples_exist:
                            return {
                                'msg': 'Cannot delete booking with samples',
                                'delete': False
                            }

            for bk_details in booking_details:
                bk_queue = self.session.query(LabServicesQueue).filter(LabServicesQueue.booking_id == bk_details.id).first()
                if bk_queue:
                    self.session.delete(bk_queue)
                self.session.delete(bk_details)
            self.session.commit()
            return {
                'msg': 'Booking deleted successfully',
                'delete': True
            }
        except Exception as e:
            self.session.rollback()
            logging.error(f"Error occurred: {e}")
            return {
                'msg': f'Error occurred: {str(e)}',
                'delete': False
            }

    def update_transaction_booking_status_based_on_procesed_result(
            self, queue_id: int) -> int:

        queue = self.session.query(LabServicesQueue).filter(LabServicesQueue.id == queue_id).first()

        if not queue:
            return 0
        booking_id = queue.booking.booking.id
        percentage_complete = self.get_booking_completion_status(booking_id)
        if percentage_complete == 100:
            # update service booking to complete
            self.update_booking_status(booking_id, BookingStatus.Processed)

        return percentage_complete

    def update_booking_status(self, booking_id: int,
                              booking_status: BookingStatus):
        booking = self.session.query(ServiceBooking).filter(ServiceBooking.id == booking_id).first()
        if booking:
            booking.booking_status = booking_status
            self.session.commit()

    def get_booking_completion_status(self, booking_id: int) -> int:
        # get all service booking related to this booking_id
        all_services = self.get_booking_details_by_booking_id(booking_id)
        #
        # print('booking details id', booking_id)
        complete = 0
        no_of_waiting_service = 0
        for serv in all_services:
            # queue = self.queue_repo.get_queue_by_booking_id(serv['id'])
            queue = self.session.query(LabServicesQueue).filter(LabServicesQueue.booking_id == serv.id).first()

            if queue is not None:
                # check observation result is ready
                if queue.status == QueueStatus.Waiting:
                    no_of_waiting_service = no_of_waiting_service + 1

                if queue.lab_service.lab_type == LabType.Observation and queue.lab_result is not None:
                    complete = complete + 1
                    continue

                # check experiment result is ready
                sample = self.session.query(CollectedSamples).filter(CollectedSamples.queue_id == queue.id).first()
                if sample:
                    # the sample is completely processed
                    if sample.status == QueueStatus.Processed:
                        complete = complete + 1

        # get number of LabServiceQueue with waiting status for this booking id


        no_of_booked_services = len(all_services) - no_of_waiting_service

        if no_of_booked_services == 0:
            no_of_booked_services = 1

        percentage_complete = (complete / no_of_booked_services) * 100
        return percentage_complete

    def update_business_service(self, service_id: int, updated_service: dict) -> Optional[BusinessServices]:
        """Update a service by its ID."""
        service = self.session.query(BusinessServices).filter(BusinessServices.service_id == service_id).first()
        if service:
            for key, value in updated_service.items():
                setattr(service, key, value)
            self.session.commit()
            self.session.refresh(service)
            return service
        return None

    def get_business_service_by_id(self, id: int) -> BusinessServiceDTO:
        business_service = self.session.query(BusinessServices).filter(BusinessServices.service_id == id).one_or_none()
        if business_service:
            return BusinessServiceDTO.from_orm(business_service)
        return None
