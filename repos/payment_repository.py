from typing import List

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from dtos.transaction import PaymentDTO, TransactionDTO
from models.auth import User
from models.client import Person
from models.transaction import Transaction
from models.services import ServiceBooking
from models.transaction import Payments, ServiceType
from repos.auth_repository import UserRepository
from repos.client.client_repository import ClientRepository


class PaymentRepository:

    def __init__(self, db_session: Session):
        self.db_session = db_session
        # usr = get_current_user()

        self.user_id = 1  # usr.id

    def create_payment(self, payment: PaymentDTO) -> PaymentDTO:
        payment.user_id = self.user_id
        db_payment = Payments(**payment.dict())
        self.db_session.add(db_payment)
        self.db_session.commit()
        self.db_session.refresh(db_payment)

        return PaymentDTO(
            id=db_payment.id,
            payment_date=db_payment.payment_date,
            payment_time=db_payment.payment_time,  # for response only
            amount=db_payment.amount,
            transaction_id=db_payment.transaction_id,
            payment_method=db_payment.payment_method
        )

    def get_payment(self, payment_id: int) -> TransactionDTO:
        return self.db_session.query(Payments).filter(Payments.id == payment_id).first()

    def get_transaction_payments(self, transaction_id: int) -> List[Payments]:
        return self.db_session.query(Payments).filter(Payments.transaction_id == transaction_id).all()

    def update_payment(self, payment_id: int, payment: PaymentDTO):
        db_payment = self.db_session.query(Payments).filter(Payments.id == payment_id).first()
        if db_payment:
            for key, value in payment.dict().items():
                setattr(db_payment, key, value)
            self.db_session.commit()
            self.db_session.refresh(db_payment)
        return db_payment

    def delete_payment(self, payment_id: int):
        db_payment = self.db_session.query(Payments).filter(Payments.id == payment_id).first()
        if db_payment:
            self.db_session.delete(db_payment)
            self.db_session.commit()
        return db_payment

    def get_payments_by_transaction_id(db: Session, transaction_id: int) -> List[Payments]:
        return db.query(Payments).filter(Payments.transaction_id == transaction_id).all()

    def get_receipt_details(self, db: Session, transaction_id: int):
        # Lab transaction details

        transaction = self.get_transaction_by_id(transaction_id)
        user = UserRepository(db).get_user_by_id(transaction.user_id)
        cli_repo = ClientRepository(db)
        usr_info = cli_repo.get_client(user.person_id)
        user = {
            'name': usr_info.first_name + ' ' + usr_info.last_name,
            'username': user.username
        }

        # sales

        # services

        # lab services

        return {

        }

    #
    # def get_payments(self, limit=20, skip=0, transaction_type=ServiceType.All, client_id=0,
    #                  start_date: str = '', last_date: str = ''):
    #     cols = [Payments.id,
    #             Payments.payment_date,
    #             Payments.payment_method,
    #             Payments.payment_time,
    #             Payments.user_id,
    #             Payments.amount,
    #             Payments.transaction_id,
    #             ServiceBooking.client_id,
    #             Person.last_name.label('processing_agent_last_name'),
    #             Person.last_name.label('processing_agent_first_name'),
    #             func.sum(Payments.amount).label('total_amount')]
    #
    #     rs = self.db_session.query(*cols).select_from(Payments) \
    #         .join(User, User.id == Payments.user_id) \
    #         .join(Person, Person.id == User.person_id) \
    #         .join(Transaction, Transaction.id == Payments.transaction_id) \
    #         .join(ServiceBooking, ServiceBooking.transaction_id == Transaction.id) \
    #
    #     if client_id != 0:
    #         rs = rs.filter(ServiceBooking.client_id == client_id)
    #
    #     if len(start_date) >= 8 and len(last_date) >= 8:
    #         rs = rs.filter(
    #             and_(
    #                 Payments.payment_date >= start_date,
    #                 Payments.payment_date <= last_date)
    #
    #         )
    #     total = rs.all()[0].total_amount;
    #     extracts = rs.group_by(
    #         Payments.id,
    #         Payments.payment_date,
    #         Payments.payment_method,
    #         Payments.payment_time,
    #         Payments.user_id,
    #         Payments.amount,
    #         Payments.transaction_id,
    #         Person.last_name,
    #         Person.first_name
    #     )
    #
    #     responds = extracts.offset(skip).limit(limit).all()
    #
    #     payments = []
    #     for payment in responds:
    #         payments.append({
    #             'id': payment.id,
    #             'payment_time': payment.payment_time,
    #             'payment_date': payment.payment_date,
    #             'payment_amount': payment.amount,
    #             'processed_by': payment.processing_agent_last_name + ' ' + payment.processing_agent_last_name,
    #             'transaction_id': payment.transaction_id,
    #             'payment_method': payment.payment_method
    #         })
    #
    #     return {
    #         'data': payments,
    #         'total': extracts.count(),
    #         'volume': total
    #     }

    def get_payments(self, limit=20, skip=0, transaction_type=ServiceType.All, client_id=0,
                     start_date: str = '', last_date: str = ''):
        # Define columns to select
        cols = [
            Payments.id,
            Payments.payment_date,
            Payments.payment_method,
            Payments.payment_time,
            Payments.user_id,
            Payments.amount,
            Payments.transaction_id,
            ServiceBooking.client_id,
            Person.last_name.label('processing_agent_last_name'),
            Person.first_name.label('processing_agent_first_name'),  # ✅ Corrected first name
            func.sum(Payments.amount).over().label('total_amount')  # ✅ Moved to window function
        ]

        # Base query
        rs = self.db_session.query(*cols).select_from(Payments) \
            .join(User, User.id == Payments.user_id) \
            .join(Person, Person.id == User.person_id) \
            .join(Transaction, Transaction.id == Payments.transaction_id) \
            .join(ServiceBooking, ServiceBooking.transaction_id == Transaction.id)

        # Filter by client_id if provided
        if client_id != 0:
            rs = rs.filter(ServiceBooking.client_id == client_id)

        # Apply date filters if valid dates are provided
        if len(start_date) >= 8 and len(last_date) >= 8:
            rs = rs.filter(
                and_(
                    Payments.payment_date >= start_date,
                    Payments.payment_date <= last_date
                )
            )

        # Apply GROUP BY to avoid errors
        rs = rs.group_by(
            Payments.id,
            Payments.payment_date,
            Payments.payment_method,
            Payments.payment_time,
            Payments.user_id,
            Payments.amount,
            Payments.transaction_id,
            ServiceBooking.client_id,
            Person.last_name,
            Person.first_name
        )

        # Get total amount correctly
        total_amount_query = self.db_session.query(func.sum(Payments.amount)).scalar() or 0

        # Apply pagination
        responds = rs.offset(skip).limit(limit).all()

        # Format response
        payments = [
            {
                'id': payment.id,
                'payment_time': payment.payment_time,
                'payment_date': payment.payment_date,
                'payment_amount': payment.amount,
                'processed_by': f"{payment.processing_agent_last_name} {payment.processing_agent_first_name}",
                'transaction_id': payment.transaction_id,
                'payment_method': payment.payment_method
            }
            for payment in responds
        ]

        return {
            'data': payments,
            'total': rs.count(),  # ✅ Uses correct grouped query
            'volume': total_amount_query  # ✅ Uses correct sum calculation
        }
