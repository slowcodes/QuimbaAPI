from operator import and_
from typing import List, Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import JSONResponse

from dtos.auth import UserDTO
from dtos.lab import DateFilterDTO
from dtos.transaction import TransactionDTO, PaymentDTO, ReferredTransactionDTO, TransactionPackageDTO
from db import get_db
from models.services import BookingStatus
from models.transaction import ServiceType, TransactionType
from repos import transaction_repository
from repos.client.referral_repository import ReferralRepository
from repos.consultation_repository import ConsultationRepository
from repos.lab.lab_repository import LabRepository
from repos.payment_repository import PaymentRepository
from repos.transaction_repository import TransactionRepository
from security.dependencies import get_current_active_user, require_role, require_access_privilege

transaction_router = APIRouter(prefix="/api/transaction", tags=["Transaction"])


def transaction_repo(db: Session = Depends(get_db)) -> TransactionRepository:
    return TransactionRepository(db)


def lab_repository(db: Session = Depends(get_db)) -> LabRepository:
    return LabRepository(db)


def consultation_repo(db: Session = Depends(get_db)) -> ConsultationRepository:
    return ConsultationRepository(db)


def referral_repository(db: Session = Depends(get_db)) -> ReferralRepository:
    return ReferralRepository(db)


def payment_repo(db: Session = Depends(get_db)) -> PaymentRepository:
    return PaymentRepository(db)


@transaction_router.get("/")
def get_transaction(transaction_id: int,
                    # current_user: Annotated[UserDTO, Depends(require_access_privilege(11))],
                    repo: TransactionRepository = Depends(transaction_repo),
                    cons_repo: ConsultationRepository = Depends(consultation_repo),
                    lab_repo: LabRepository = Depends(lab_repository)):
    lab_services = lab_repo.get_lab_services_booking(transaction_id)
    transaction_details = repo.get_laboratory_transaction(transaction_id)
    consultation_services = cons_repo.get_consultation_service_booking(transaction_id)

    if transaction_details is not None:
        all_service = lab_services + consultation_services
        transaction_details['services'] = all_service
        return transaction_details

    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                        content={'data': {}, 'error': True, 'msg': 'Invalid Transaction ID'})


@transaction_router.get("/open")
def get_open_transactions(
        # transaction_type: TransactionType = TransactionType.All,
        limit: int = 100, skip: int = 0,
        repo: TransactionRepository = Depends(transaction_repo)):
    open_transactions = repo.get_clients_with_open_transactions(limit=limit, skip=skip)
    return open_transactions


@transaction_router.post("/transaction-package/")
def add_transaction_package(
        transaction_package: TransactionPackageDTO,
        repo: TransactionRepository = Depends(transaction_repo)):
    transaction_package = repo.create_transaction_package(transaction_package)
    if transaction_package is None:
        raise HTTPException(status_code=400, detail="Transaction package creation failed")
    return transaction_package


@transaction_router.post('/')
def add_booking(tc: TransactionDTO,
                repo: TransactionRepository = Depends(transaction_repo),
                ref_repo: ReferralRepository = Depends(referral_repository)):
    txn = repo.create_transaction(tc.discount)

    if tc.referral_id != 0:
        ref = ReferredTransactionDTO(
            transaction_id=txn["id"],
            referral_id=tc.referral_id
        )
        ref_repo.create_referred_transaction(ref)
    return JSONResponse(status_code=status.HTTP_201_CREATED,
                        content={"data": txn, "error": False, "msg": "Transaction added successfully"})


@transaction_router.get("/laboratories/")
def read_collated_results(limit: int = 15, skip: int = 0, booking_status: BookingStatus = BookingStatus.Processing,
                          lab_id: int = 0, search_text: str = '', client_id: int = 0,
                          only_referred_transactions: int = 0,
                          start_date: str = '', last_date: str = '', date_filter_status: str = '',
                          transaction_type: TransactionType = TransactionType.All,
                          repo: TransactionRepository = Depends(transaction_repo),
                          ):
    date_filter: DateFilterDTO = {
        "start_date": start_date,
        "last_date": last_date,
        "status": date_filter_status
    }
    ref_flag = False
    if only_referred_transactions == 1:
        ref_flag = True
    print('flag', ref_flag)
    results = repo.get_laboratory_transaction_details(limit, skip, lab_id, booking_status, search_text, client_id,
                                                      date_filter, transaction_type, ref_flag)

    if results is None:
        raise HTTPException(status_code=204, detail="No content found")
    return results


@transaction_router.get("/transactions/{transaction_id}/payments", tags=["Payment"], response_model=List[PaymentDTO])
def get_payments_by_transaction(transaction_id: int, db: Session = Depends(get_db)):
    prp = PaymentRepository(db)
    payments = prp.get_payments_by_transaction_id(db, transaction_id=transaction_id)
    if not payments:
        raise HTTPException(status_code=404, detail="No payments found for this transaction")
    return payments


@transaction_router.post("/payments/", response_model=PaymentDTO, tags=["Payment"])
def create_payment(payment: PaymentDTO,
                   db: Session = Depends(get_db)):
    repo = PaymentRepository(db)
    return repo.create_payment(payment=payment)


@transaction_router.get("/payments/{payment_id}", response_model=PaymentDTO, tags=["Payment"])
def read_payment(payment_id: int,
                 db: Session = Depends(get_db)):
    prp = PaymentRepository(db)
    db_payment = prp.get_payment(db=db, payment_id=payment_id)
    if db_payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return db_payment


@transaction_router.put("/payments/{payment_id}", response_model=PaymentDTO)
def update_payment(payment_id: int,
                   payment: PaymentDTO,
                   db: Session = Depends(get_db)):
    db_payment = transaction_repository.update_payment(db=db, payment_id=payment_id, payment=payment)
    if db_payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return db_payment


@transaction_router.delete("/payments")
def delete_payment(payment_id: int,
                   repo: PaymentRepository = Depends(payment_repo)):
    payment = repo.delete_payment(payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@transaction_router.get("/payments/", tags=["Payment"])
def get_payments(limit: int = 15, skip: int = 0,
                 transaction_type: TransactionType = TransactionType.All,
                 client_id: int = 0, start_date: str = '', last_date: str = '', date_filter_status: str = '',
                 repo: PaymentRepository = Depends(payment_repo)):
    return repo.get_payments(limit, skip, transaction_type, client_id,
                             start_date, last_date)
