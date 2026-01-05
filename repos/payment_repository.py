from typing import List

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from dtos.transaction import PaymentDTO, TransactionDTO
from models.auth import User
from models.client import Person
from models.transaction import Transaction, PaymentMethod
from models.services.services import ServiceBooking
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

    def get_payments(self, limit=20, skip=0, transaction_type: str = None, client_id=0,
                     start_date: str = '', last_date: str = ''):

        # Base query
        rs = self.db_session.query(Payments)
        if transaction_type:
            try:
                method = PaymentMethod(transaction_type)
                print("we applied filter")
                rs = rs.filter(Payments.payment_method == method)
            except ValueError:
                pass

        if client_id != 0:
            rs = rs.join(Transaction, Payments.transaction_id == Transaction.id) \
                .join(ServiceBooking.transaction_id == Transaction.id) \
                .filter(ServiceBooking.client_id == client_id)

        # Apply date filters if valid dates are provided
        if len(start_date) >= 8 and len(last_date) >= 8:
            rs = rs.filter(
                and_(
                    Payments.payment_date >= start_date,
                    Payments.payment_date <= last_date
                )
            )

        # get total amount before pagination
        total_amount_query = sum(t.amount for t in rs if t.amount is not None)

        # Apply GROUP BY to avoid errors
        # rs = rs.group_by(
        #     Payments.id,
        #     Payments.payment_date,
        #     Payments.payment_method,
        #     Payments.payment_time,
        #     Payments.user_id,
        #     Payments.amount,
        #     Payments.transaction_id,
        #     ServiceBooking.client_id,
        #     Person.last_name,
        #     Person.first_name
        # )
        # Apply pagination
        response = rs.offset(skip).limit(limit).all()

        # Format response
        payments = [PaymentDTO.from_orm(payment) for payment in response]

        return {
            'data': payments,
            'total': rs.count(),  # ✅ Uses correct grouped query
            'volume': total_amount_query  # ✅ Uses correct sum calculation
        }
