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

    def computeTransactionTotal(self, transaction_id: int):
        from repos.transaction_repository import TransactionRepository

        def _as_list(value):
            return value if isinstance(value, list) else []

        def _get_price(value):
            return value if isinstance(value, (int, float)) else 0

        def _get_bundle_price(package):
            collections = package.get("lab_service_bundle") or package.get("lab_collections") or []
            original_total = 0
            for collection in _as_list(collections):
                lab_service = collection.get("lab_service") or {}
                business_service = lab_service.get("business_service") or {}
                price_code = business_service.get("pc") or {}
                original_total += _get_price(price_code.get("service_price"))

            discount = _get_price(package.get("discount"))
            if discount <= 0:
                return original_total, original_total
            if discount <= 1:
                discounted_total = original_total * (1 - discount)
            elif discount <= 100:
                discounted_total = original_total * (1 - (discount / 100))
            else:
                discounted_total = max(0, original_total - discount)
            return original_total, discounted_total

        def _compute_lab_service_total_price(labs):
            total = 0
            for lab in _as_list(labs):
                booking = lab.get("booking") or {}
                price_code = (booking.get("price_code_rel") or {})
                total += _get_price(price_code.get("service_price"))
            return total

        transaction = TransactionRepository(self.db_session).get_by_id(transaction_id)
        if not transaction:
            return None

        services = transaction.get("sales_services") or {}

        consultations = _as_list(services.get("consultation_services"))
        labs = _as_list(services.get("lab_services"))
        dispensary = _as_list(services.get("dispensary_services"))
        enrollment = _as_list(services.get("enrollment"))

        consultation_total = sum(_get_price(s.get("price")) for s in consultations)
        enrollment_total = sum(_get_price(s.get("price")) for s in enrollment)
        lab_total = _compute_lab_service_total_price(labs)
        dispensary_total = sum(
            _get_price(d.get("selling_price")) * (d.get("quantity") or 1)
            for d in dispensary
        )

        lab_promo = 0
        for promo in _as_list(transaction.get("package_transactions")):
            original, discounted = _get_bundle_price(promo.get("package") or {})
            lab_promo += (original - discounted)

        subtotal = enrollment_total + consultation_total + lab_total + dispensary_total

        discount = transaction.get("discount")
        discount_value = _get_price(discount)
        total = subtotal - discount_value - lab_promo

        payments = _as_list(transaction.get("payment"))
        total_paid = sum(_get_price(p.get("amount")) for p in payments)

        balance = total - total_paid

        return {
            "consultationTotal": consultation_total,
            "labTotal": lab_total,
            "dispensaryTotal": dispensary_total,
            "subtotal": subtotal,
            "discount": discount,
            "total": total,
            "totalPaid": total_paid,
            "balance": balance,
        }

    def create_payment(self, payment: PaymentDTO) -> PaymentDTO:
        payment.user_id = self.user_id
        db_payment = Payments(**payment.dict())
        self.db_session.add(db_payment)
        self.db_session.commit()
        self.db_session.refresh(db_payment)

        # update transaction status to closed if full payment
        transaction = self.db_session.query(Transaction).filter(Transaction.id == db_payment.transaction_id).first()
        if transaction:
            total_paid = sum(p.amount for p in transaction.payment)
            if total_paid >= self.computeTransactionTotal(transaction.id)["total"]:
                transaction.status = 'Closed'
                self.db_session.commit()

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

    def get_payments(self, limit=20, skip=0, transaction_type: str = None, client_id=0,
                     start_date: str = '', last_date: str = ''):

        # Base query
        rs = self.db_session.query(Payments)
        if transaction_type:
            try:
                method = PaymentMethod(transaction_type)
                rs = rs.filter(Payments.payment_method == method)
            except ValueError:
                pass

        if client_id != 0:
            rs = rs.join(Transaction, Payments.transaction_id == Transaction.id) \
                .join(ServiceBooking, ServiceBooking.transaction_id == Transaction.id) \
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

        response = rs.offset(skip).limit(limit).all()

        # Format response
        payments = [PaymentDTO.from_orm(payment) for payment in response]

        return {
            'data': payments,
            'total': rs.count(),  # ✅ Uses correct grouped query
            'volume': total_amount_query  # ✅ Uses correct sum calculation
        }
