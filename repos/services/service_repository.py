from typing import List
import logging

from sqlalchemy.orm import Session

import db
from commands.services import ServiceBookingDTO, ServiceBookingDetailDTO, ServiceEventDTO, EventType
from models.client import Client, Person
from models.lab.lab import CollectedSamples, LabBundleCollection, LabServicesQueue, QueueStatus
from models.services import Bundles, ServiceBooking, PriceCode, ServiceBookingDetail, BookingStatus, \
    ServiceClinicalExamination
from models.transaction import Transaction


class ServiceRepository:
    def __init__(self, session: Session):
        self.session = session

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
        db_service_booking_details = ServiceBookingDetail(**service_booking.dict())
        self.session.add(db_service_booking_details)
        self.session.commit()
        self.session.refresh(db_service_booking_details)

        print('service booking details', db_service_booking_details.__dict__)
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

    def get_service_booking_transaction_id(self, transaction_id: int) -> ServiceBookingDTO:
        return self.session.query(ServiceBooking).filter(ServiceBooking.transaction_id == transaction_id).first()

    def get_all_service_bookings(self, limit: int, skip: int, client_id: int = 0) -> dict:
        cols = [
            Person.first_name,
            Person.last_name,
            ServiceBooking.transaction_id,
            ServiceBooking.client_id,
            ServiceBooking.booking_type,
            ServiceBooking.booking_status,
            Transaction.transaction_time,
            ServiceBooking.id.label("booking_id")
        ]

        query = self.session.query(*cols).select_from(ServiceBooking) \
            .join(Client, Client.id == ServiceBooking.client_id) \
            .join(Person, Client.person_id == Person.id) \
            .join(Transaction, ServiceBooking.transaction_id == Transaction.id)\

        if client_id != 0:
            query = query.filter(ServiceBooking.client_id == client_id)
        total = query.count()
        selected_booking = query.order_by(Transaction.transaction_time.desc()).offset(skip).limit(limit).all()

        data = []
        for booking in selected_booking:
            data.append(

                 {
                    'id': booking.booking_id,
                    'client_id': booking.client_id,
                    'transaction_id': booking.transaction_id,
                    'transaction_time': booking.transaction_time,
                    'client_first_name': booking.first_name,
                    'client_last_name': booking.last_name,
                    'booking_type': booking.booking_type,
                    'booking_status': booking.booking_status,
                }

            )

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

            print('delete_booking', delete_booking, service_booking.booking_type)
            if delete_booking['delete']:
                self.session.delete(service_booking)

                print('service booking deleted', service_booking.id, service_booking)
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

    def update_transaction_booking_status_based_on_sample_update(
            self, sample_id: int) -> int:
        cols = [
            ServiceBooking.transaction_id,
            Transaction.transaction_date,
            Transaction.discount,
            CollectedSamples.id,
            ServiceBooking.id.label("booking_id")
        ]

        rs = self.session.query(*cols).select_from(CollectedSamples). \
            join(LabServicesQueue, LabServicesQueue.id == CollectedSamples.queue_id). \
            join(ServiceBookingDetail, LabServicesQueue.booking_id == ServiceBookingDetail.id). \
            join(ServiceBooking, ServiceBooking.id == ServiceBookingDetail.booking_id). \
            join(Transaction, Transaction.id == ServiceBooking.transaction_id). \
            where(CollectedSamples.id == sample_id).first()

        booking_id = rs.booking_id
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
        for serv in all_services:

            # queue = self.queue_repo.get_queue_by_booking_id(serv['id'])
            queue = self.session.query(LabServicesQueue).filter(LabServicesQueue.booking_id == serv['id']).first()

            if queue is not None:
                if queue.status == QueueStatus.Processing or queue.status == QueueStatus.Processed:

                    # find it in collected samples
                    sample = self.session.query(CollectedSamples).filter(CollectedSamples.queue_id == queue.id).first()

                    if sample:
                        # the sample is completely processed
                        if sample.status == QueueStatus.Processed:
                            complete = complete + 1

        no_of_booked_services = len(all_services)

        if no_of_booked_services == 0:
            no_of_booked_services = 1

        percentage_complete = (complete / no_of_booked_services) * 100
        return percentage_complete
