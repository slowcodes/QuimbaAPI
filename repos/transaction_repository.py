from collections import defaultdict
from typing import Optional, Type, TypeVar
from datetime import datetime

from sqlalchemy import select, or_
from sqlalchemy.orm import Session, joinedload

from db import Base
from dtos.consultant import ConsultationQueueDTO
from dtos.lab import DateFilterDTO, LabServicesQueueDTO, LabResultByQueueDTO
from dtos.people import BasicClientDTO
from dtos.pharmacy.dispensed import DispensedPrescriptionRead
from dtos.transaction import TransactionDTO, TransactionPackageDTO, ReferredTransactionSettlementResponseDTO
from models.auth import User
from models.client import Person, Client
from models.consultation import ConsultationQueue, InHours, Specialist
from models.lab.lab import LabServicesQueue, LabService
from models.pharmacy import DispensedPrescriptionDetail, PrescriptionDetail, Drug
from models.sales import BusinessSales
from models.services.services import ServiceBooking, BookingStatus, Bundles, ServiceBookingDetail, BookingType
from models.transaction import Transaction, TransactionType, ReferredTransaction, PackageTransaction, \
    ReferredTransactionSettlement, ReferredTransactionSettlementDetail, ReferredTransactionStatus
from repos.services.service_repository import ServiceRepository
from utils.functions import generate_transaction_id, sqlalchemy_to_dict


class TransactionRepository:

    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.service_repository = ServiceRepository(self.db_session)

    ModelType = TypeVar("ModelType", bound=Base)

    def get_lab_transaction_packages(self, transaction_id):
        cols = [Bundles.bundles_name,
                Bundles.bundles_desc,
                Bundles.discount,
                PackageTransaction.package_id,
                PackageTransaction.transaction_id,
                ]
        rs = self.db_session.query(*cols).select_from(PackageTransaction) \
            .join(Bundles, Bundles.id == PackageTransaction.package_id) \
            .filter(PackageTransaction.transaction_id == transaction_id).all()

        if rs is None:
            return None

        package_transactions = []
        for package in rs:
            package_transactions.append(
                {
                    'id': package.package_id,
                    'bundles_name': package.bundles_name,
                    'discount': package.discount,
                    'transaction_id': package.transaction_id,
                    'lab_collections': self.service_bundle_repository.get_service_bundle_services(package.package_id)
                }
            )
        return package_transactions

    def get_by_id(self, transaction_id: int) -> TransactionDTO:
        tx = (
            self.db_session.query(Transaction)
            .options(joinedload(Transaction.package_transactions))
            .filter(Transaction.id == transaction_id)
            .first()
        )
        return self.get_list(tx, BookingType.Aggregate)

    def get_all(
            self,
            date_filter: DateFilterDTO,
            skip: int = 0,
            limit: int = 100,
            referred: bool = False,
            referral_id: Optional[int] = None
    ):
        query = self.db_session.query(Transaction)

        # --- Referral filter ---
        if referred or referral_id is not None:
            query = query.join(ReferredTransaction)
            if referred:
                query = query.filter(ReferredTransaction.referral_id.isnot(None))
            if referral_id is not None:
                query = query.filter(ReferredTransaction.referral_id == referral_id)

        # --- Date filtering ---
        if date_filter and date_filter.start_date:
            last_date = date_filter.last_date or datetime.utcnow()
            query = query.filter(
                Transaction.transaction_date.between(date_filter.start_date, last_date)
            )

        if getattr(date_filter, "status", None):
            status_value = date_filter.status
            if status_value in ("Open", "Closed"):
                query = query.filter(Transaction.transaction_status == status_value)
            # if 'all' or anything else, no status filter is applied

        # --- Count total before pagination ---
        total = query.count()

        # --- Ordering (optional but recommended) ---
        query = query.order_by(Transaction.transaction_date.desc())

        # # --- Pagination ---
        if skip:
            query = query.offset(skip)
        if limit:
            query = query.limit(limit)

        # --- Execute query ---
        results = query.all()

        # --- Return structured response ---
        return {
            "data": [self.get_list(datum, BookingType.Aggregate) for datum in results],
            "total": total
        }

    def get_all_lab(self, skip: int = 0, limit: int = 0, lab_id: int = 0, client_id: int = 0):
        query = (
            self.db_session.query(Transaction)
            .join(ServiceBooking, ServiceBooking.transaction_id == Transaction.id)
            .join(ServiceBooking.booking_detail)
            .join(ServiceBookingDetail.lab_service_queue)
            .join(LabServicesQueue.lab_service)
            .join(LabService.laboratory)
            .filter(ServiceBookingDetail.booking_type == BookingType.Laboratory)
            .distinct(Transaction.id)
            .options(
                joinedload(Transaction.sales_services)
                .joinedload(ServiceBooking.booking_detail)
                .joinedload(ServiceBookingDetail.lab_service_queue)
                .joinedload(LabServicesQueue.lab_service)
            )
        )

        if lab_id != 0:
            query = query.filter(LabService.lab_id == lab_id)

        if client_id != 0:
            query = query.filter(ServiceBooking.client_id == client_id)

        # --- Pagination ---
        total = query.count()
        if skip:
            query = query.offset(skip)
        if limit:
            query = query.limit(limit)

        return {
            'data': [self.get_list(datum, BookingType.Laboratory) for datum in query.all()],
            'total': total
        }

    def get_all_consultation(self):
        query = (
            self.db_session.query(Transaction)
            .filter(
                Transaction.sales_services.has(
                    ServiceBooking.booking_detail.any(
                        ServiceBookingDetail.consultation_queue.has()  # ✅ one-to-one → use .has()
                    )
                )
            )
            .options(
                joinedload(Transaction.sales_services)
                .joinedload(ServiceBooking.booking_detail)
                .joinedload(ServiceBookingDetail.consultation_queue)
                .joinedload(ConsultationQueue.specialization),

                joinedload(Transaction.sales_services)
                .joinedload(ServiceBooking.booking_detail)
                .joinedload(ServiceBookingDetail.consultation_queue)
                .joinedload(ConsultationQueue.schedule)
                .joinedload(InHours.consultant)
                .joinedload(Specialist.user)
                .joinedload(User.person),

                joinedload(Transaction.sales_services)
                .joinedload(ServiceBooking.booking_detail)
                .joinedload(ServiceBookingDetail.price_code_rel),
            )
        )

        return {
            'data': [self.get_list(datum, BookingType.Appointment) for datum in query.all()],
            'total': query.count()
        }

    def get_all_dispensaries(self):
        query = (
            self.db_session.query(Transaction)
            .filter(
                Transaction.sales_services.has(
                    ServiceBooking.business_sales.any(
                        BusinessSales.dispensed_prescriptions.any()
                    )  # ✅ at least one business_sales record
                )
            )
            .options(
                joinedload(Transaction.sales_services)
                .joinedload(ServiceBooking.business_sales)
                .joinedload(BusinessSales.dispensed_prescriptions)
                .joinedload(DispensedPrescriptionDetail.prescription_detail)
                .joinedload(PrescriptionDetail.drug)
                .joinedload(Drug.product)
            )
        )
        return {
            'data': [self.get_list(datum, BookingType.Dispensary) for datum in query.all()],
            'total': query.count()
        }

    def get_list(self, model: Type[ModelType], bookingType: BookingType):
        lab_list = []
        dispensary_list = []
        consultation_list = []
        enrollments = []

        if model.sales_services:
            if not model.sales_services.booking_detail:
                lab_list = []
                dispensary_list = []
                consultation_list = []
                enrollments = []
            else:
                for booking_detail in model.sales_services.booking_detail:
                    if booking_detail.booking_type == BookingType.Laboratory:

                        if booking_detail.lab_service_queue:
                            lab_list.append(LabResultByQueueDTO.from_orm(
                                booking_detail.lab_service_queue
                            ))
                    elif booking_detail.booking_type == BookingType.Enrollment:
                        enrollments.append({
                            'service_id': booking_detail.service_id,
                            'service_type': booking_detail.booking_type,
                            'service_name': 'New Client Enrollment',
                            'price': booking_detail.price_code_rel.service_price,
                            'price_code': booking_detail.price_code_rel.id,
                            'ext_turn_around_time': 10
                        })
                    elif booking_detail.booking_type == BookingType.Consultation or booking_detail.booking_type == BookingType.Appointment:
                        dtl = ConsultationQueueDTO.from_orm(
                            booking_detail.consultation_queue) if booking_detail.consultation_queue else None
                        dtl = f"Consultation - {dtl.specialization.department} with {dtl.schedule.consultant.user.person.first_name} {dtl.schedule.consultant.user.person.last_name} ({dtl.notes})" if dtl and dtl.specialization else "Consultation Service"
                        consultation_list.append({
                            'service_id': booking_detail.service_id,
                            'service_type': booking_detail.booking_type,
                            'service_name': dtl,
                            'price': booking_detail.price_code_rel.service_price,
                            'price_code': booking_detail.price_code_rel.id,
                            'ext_turn_around_time': 15
                        })

            if (
                    bookingType == BookingType.Dispensary or bookingType == BookingType.Aggregate) and model.sales_services.business_sales:

                for sale in model.sales_services.business_sales:
                    dispensed = DispensedPrescriptionRead.from_orm(
                        sale.dispensed_prescriptions[0]) if sale.dispensed_prescriptions else None
                    if dispensed:
                        dispensary_list.append({
                            'pack': dispensed.sale.package.package_container.value,
                            'selling_price': dispensed.sale.package.sales_price_code.selling_price,
                            'quantity': dispensed.sale.quantity if dispensed else 0,
                            'product': dispensed.sale.product.product_name,
                            'prescription': {
                                'product': dispensed.prescription_detail.drug.product.product_name,
                                'form': dispensed.prescription_detail.form,
                                'frequency': dispensed.prescription_detail.frequency,
                                'duration': dispensed.prescription_detail.duration,
                                'dosage': dispensed.prescription_detail.dosage
                            } if dispensed.prescription_detail else None
                        })

        tx = TransactionDTO.from_orm(model)  # serialize to get necessary fields
        print("Transaction", tx.id)

        if tx.sales_services:
            tx.sales_services.lab_booking_completion = self.service_repository.get_booking_completion_status(
                tx.sales_services.id)
        tx = tx.dict()


        if not tx.get('sales_services'):
            tx['sales_services'] = {}
        if bookingType in (
                BookingType.Consultation,
                BookingType.Appointment,
                BookingType.Aggregate):
            tx['sales_services']['consultation_services'] = consultation_list
        if bookingType == BookingType.Laboratory or bookingType == BookingType.Aggregate:
            tx['sales_services']['lab_services'] = lab_list
        if bookingType == BookingType.Dispensary or bookingType == BookingType.Aggregate:
            tx['sales_services']['dispensary_services'] = dispensary_list
        if bookingType == BookingType.Enrollment or bookingType == BookingType.Aggregate:
            tx['sales_services']['enrollment'] = enrollments

        return tx

    def get_all_enrollment(self, skip: int = 0, limit: int = 100):

        query = (
            self.db_session.query(Transaction)
            .join(Transaction.sales_services)
            .join(ServiceBooking.booking_detail)
            .join(ServiceBookingDetail.business_service)
            .filter(
                ServiceBookingDetail.booking_type == BookingType.Enrollment)  # ensures there is at least one LabServicesQueue
            .options(
                joinedload(Transaction.sales_services)
                .options(
                    joinedload(ServiceBooking.booking_detail)
                    .options(
                        joinedload(ServiceBookingDetail.business_service)
                    )
                )
            )
        )

        total = query.count()

        if skip:
            query = query.offset(skip)
        if limit:
            query = query.limit(limit)

        return {
            'data': [self.get_list(datum, BookingType.Laboratory) for datum in query.all()],
            'total': total
        }

    # generate services list
    def get_all_referred_transactions(self):
        pass

    def tid_exist(self, tid: int) -> bool:
        exits = self.db_session.query(Transaction).filter(Transaction.id == tid)
        if exits is not None:
            return True
        return False

    def create_transaction(self, discount: float, user_id: int):
        tid = generate_transaction_id()

        continue_tid_generation = True
        while continue_tid_generation:
            continue_tid_generation = not self.tid_exist(tid)

        new_transaction = Transaction(id=tid, user_id=user_id, discount=discount)
        self.db_session.add(new_transaction)
        self.db_session.commit()

        # Serialize Transaction object into dictionary
        transaction_dict = {
            "id": new_transaction.id,
            "transaction_date": new_transaction.transaction_date.strftime('%Y-%m-%d'),
            # Serialize Transaction object into dictionary #new_transaction.transaction_date,
            "transaction_time": new_transaction.transaction_time.strftime('%Y-%m-%d %H:%M:%S'),
            "discount": new_transaction.discount,
            "user_id": new_transaction.user_id
        }
        return transaction_dict

    def create_transaction_package(self, transaction_package: TransactionPackageDTO) -> TransactionPackageDTO:
        pt = PackageTransaction(transaction_id=transaction_package.transaction_id,
                                package_id=transaction_package.package_id)
        self.db_session.add(pt)
        self.db_session.commit()
        self.db_session.refresh(pt)
        return TransactionPackageDTO.from_orm(pt)

    def get_transaction_by_id(self, transaction_id: int) -> TransactionDTO:
        return TransactionDTO.from_orm(
            self.db_session.query(Transaction).filter(Transaction.id == transaction_id).first()
        )

    def update_transaction_discount(self, transaction_id: int, new_discount: float):
        transaction = self.get_transaction_by_id(transaction_id)
        if transaction:
            transaction.discount = new_discount
            self.db_session.commit()
            return transaction
        return None

    def delete_transaction(self, transaction_id: int):
        transaction = self.get_transaction_by_id(transaction_id)
        if transaction:
            self.db_session.delete(transaction)
            self.db_session.commit()
            return transaction
        return None

    def get_clients_with_open_transactions(self,
                                           limit: int = 100, skip: int = 0):
        stmt = (
            select(Client, Transaction)
            .join(ServiceBooking, Client.id == ServiceBooking.client_id)
            .join(Transaction, ServiceBooking.transaction_id == Transaction.id)
            .where(Transaction.transaction_status == TransactionType.Open)
        )

        rows = self.db_session.execute(stmt).all()

        # Group transactions per user
        grouped = defaultdict(list)
        for client, transaction in rows:
            grouped[client].append(transaction)

        results = []
        for client, transactions in grouped.items():
            results.append({
                "client": BasicClientDTO.from_orm(client),
                "transactions": [
                    self.get_list(t, BookingType.Aggregate)
                    for t in transactions
                ]
            })

        return results

    def get_settlement(
            self,
            limit: int,
            skip: int,
            start_date: str = '',
            last_date: str = '',
            referral_id: int = 0,
            search_text: str = ''
    ):
        query = self.db_session.query(ReferredTransactionSettlement)
        search_text = (search_text or '').strip()

        if referral_id:
            query = query.filter(ReferredTransactionSettlement.created_for == referral_id)

        if start_date and last_date:
            query = query.filter(
                ReferredTransactionSettlement.created_at.between(start_date, last_date)
            )
        elif start_date:
            query = query.filter(ReferredTransactionSettlement.created_at >= start_date)
        elif last_date:
            query = query.filter(ReferredTransactionSettlement.created_at <= last_date)

        if search_text:
            query = (
                query.join(ReferredTransactionSettlement.referral)
                .join(Person)
                .filter(
                    or_(
                        Person.first_name.ilike(f"%{search_text}%"),
                        Person.last_name.ilike(f"%{search_text}%"),
                        Person.middle_name.ilike(f"%{search_text}%"),
                        Person.phone.ilike(f"%{search_text}%")
                    )
                )
            )

        count = query.count()
        if skip:
            query = query.offset(skip)
        if limit:
            query = query.limit(limit)

        st = query.all()

        results = []
        for settlement in st:
            # base settlement fields
            dto = ReferredTransactionSettlementResponseDTO.from_orm(settlement).dict()

            # replace each transaction payload with the fully built version from get_by_id
            details = []
            for detail in settlement.settlement_detail:
                tx_full = self.get_by_id(detail.ref_transaction_id) if detail.ref_transaction_id else None
                details.append({
                    "id": detail.id,
                    "ref_transaction_id": detail.ref_transaction_id,
                    "transaction": tx_full
                })

            dto["settlement_detail"] = details
            results.append(dto)

        return {
            'data': results,
            'total': count
        }

    def create_settlement(self,
                          created_for: int,
                          commission: float,
                          created_by: int,
                          ref_transaction_ids: list[int]
                          ) -> ReferredTransactionSettlement:

        settlement = ReferredTransactionSettlement(
            created_for=created_for,
            commission=commission,
            created_by=created_by
        )

        self.db_session.add(settlement)
        self.db_session.flush()  # ensures settlement.id is generated

        details = []

        for tx_id in ref_transaction_ids:
            # create settlement detail
            detail = ReferredTransactionSettlementDetail(
                settlement_id=settlement.id,
                ref_transaction_id=tx_id
            )
            details.append(detail)

            # update referred transaction status
            ref = (
                self.db_session.query(ReferredTransaction)
                .filter(ReferredTransaction.transaction_id == tx_id)
                .first()
            )
            if ref:
                ref.status = ReferredTransactionStatus.Settled

        self.db_session.add_all(details)
        self.db_session.commit()
        self.db_session.refresh(settlement)

        return ReferredTransactionSettlementResponseDTO.from_orm(settlement)
