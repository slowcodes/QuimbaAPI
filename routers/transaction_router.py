from typing import List, Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import JSONResponse

from dtos.auth import UserDTO
from dtos.lab import DateFilterDTO
from dtos.transaction import TransactionDTO, PaymentDTO, ReferredTransactionDTO, TransactionPackageDTO, \
    TransactionCreateDTO, ReferredTransactionSettlementResponseDTO, ReferredTransactionSettlementCreateDTO
from db import get_db
from models.services.services import BookingStatus
from models.transaction import TransactionType, ReferredTransactionSettlementDetail, PaymentMethod
from repos import transaction_repository
from repos.client.referral_repository import ReferralRepository
from repos.consultation.consultant_repository import ConsultantRepository
from repos.payment_repository import PaymentRepository
from repos.transaction_repository import TransactionRepository
from security.dependencies import get_current_active_user

transaction_router = APIRouter(prefix="/api/transaction", tags=["Transaction"])


def transaction_repo(db: Session = Depends(get_db)) -> TransactionRepository:
    return TransactionRepository(db)


def consultation_repo(db: Session = Depends(get_db)) -> ConsultantRepository:
    return ConsultantRepository(db)


def referral_repository(db: Session = Depends(get_db)) -> ReferralRepository:
    return ReferralRepository(db)


def payment_repo(db: Session = Depends(get_db)) -> PaymentRepository:
    return PaymentRepository(db)


@transaction_router.get("/")
def get_transaction(transaction_id: int,
                    current_user: Annotated[UserDTO, Depends(get_current_active_user)],
                    repo: TransactionRepository = Depends(transaction_repo),
                    ):
    ftd = jsonable_encoder(
        repo.get_by_id(transaction_id)
    )
    if ftd is not None:
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content={'data': ftd, 'error': False, 'msg': 'Transaction fetched successfully'})
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                        content={'data': {}, 'error': True, 'msg': 'Invalid Transaction ID'})


@transaction_router.get("/lab_service/{lab_service_id}")
def get_transaction_by_lab_service(lab_service_id: int,
                                # current_user: Annotated[UserDTO, Depends(get_current_active_user)],
                                repo: TransactionRepository = Depends(transaction_repo),
                                start_date: str = '', last_date: str = '',
                                ):
    return repo.get_lab_service_transactions_by_lab_id(lab_service_id, start_date, last_date)


@transaction_router.get("/open")
def get_open_transactions(
        # transaction_type: TransactionType = TransactionType.All,
        limit: int = 100, skip: int = 0,
        repo: TransactionRepository = Depends(transaction_repo),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    open_transactions = repo.get_clients_with_open_transactions(limit=limit, skip=skip)
    return open_transactions


@transaction_router.post("/transaction-package/")
def add_transaction_package(
        transaction_package: TransactionPackageDTO,
        repo: TransactionRepository = Depends(transaction_repo),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    transaction_package = repo.create_transaction_package(transaction_package)
    if transaction_package is None:
        raise HTTPException(status_code=400, detail="Transaction package creation failed")
    return transaction_package


@transaction_router.post('/')
def add_booking(tc: TransactionCreateDTO,
                current_user: Annotated[UserDTO, Depends(get_current_active_user)],
                repo: TransactionRepository = Depends(transaction_repo),
                ref_repo: ReferralRepository = Depends(referral_repository)):
    txn = repo.create_transaction(tc.discount, current_user.id)

    if tc.referral_id != 0:
        ref = ReferredTransactionDTO(
            transaction_id=txn["id"],
            referral_id=tc.referral_id
        )
        ref_repo.create_referred_transaction(ref)
    return JSONResponse(status_code=status.HTTP_201_CREATED,
                        content={"data": txn, "error": False, "msg": "Transaction added successfully"})


@transaction_router.get("/{path}")
def read_transactions(path: str, limit: int = 15, skip: int = 0,
                      booking_status: BookingStatus | None = None,
                      lab_id: int = 0, search_text: str = '', client_id: int = 0,
                      only_referred_transactions: int = 0,
                      start_date: str = '', last_date: str = '', date_filter_status: str = '',
                      transaction_type: TransactionType = TransactionType.All,
                      repo: TransactionRepository = Depends(transaction_repo),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    date_filter = DateFilterDTO(
        start_date=start_date + " 00:00:00" if start_date else None,
        last_date=last_date + " 23:59:59" if last_date else None,
        status=transaction_type
    )

    if path == 'laboratories':
        results = repo.get_all_lab(
            date_filter=date_filter,
            skip=skip,
            limit=limit,
            lab_id=lab_id,
            client_id=client_id,
            booking_status=booking_status,
            search_text=search_text
        )
    elif path == 'consultation':
        results = repo.get_all_consultation()
    elif path == 'dispensaries':
        results = repo.get_all_dispensaries()
    elif path == 'enrollments':
        results = repo.get_all_enrollment()
    elif path == 'all':
        results = repo.get_all(
            date_filter=date_filter,
            skip=skip,
            limit=limit,
            client_id=client_id,
            booking_status=booking_status
        )
    elif path == 'referred':
        ref_id = None if only_referred_transactions == 0 else only_referred_transactions
        results = repo.get_all(date_filter, skip, limit, True, ref_id, booking_status=booking_status)
    else:
        results = repo.get_all()
        # all_trx = [sales_services_repo.get_full_transaction_details(trx.id) for trx in results['data']]
        # result = {'data': all_trx, 'total': tx['total']}

    if results is None:
        raise HTTPException(status_code=204, detail="No content found")
    return results


@transaction_router.get("/transactions/{transaction_id}/payments", tags=["Payment"], response_model=List[PaymentDTO])
def get_payments_by_transaction(transaction_id: int, db: Session = Depends(get_db),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    prp = PaymentRepository(db)
    payments = prp.get_payments_by_transaction_id(db, transaction_id=transaction_id)
    if not payments:
        raise HTTPException(status_code=404, detail="No payments found for this transaction")
    return payments


@transaction_router.post("/payments/", response_model=PaymentDTO, tags=["Payment"])
def create_payment(payment: PaymentDTO,
                   db: Session = Depends(get_db),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    repo = PaymentRepository(db)
    return repo.create_payment(payment=payment)


@transaction_router.get("/payments/{payment_id}", response_model=PaymentDTO, tags=["Payment"])
def read_payment(payment_id: int,
                 db: Session = Depends(get_db),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    prp = PaymentRepository(db)
    db_payment = prp.get_payment(db=db, payment_id=payment_id)
    if db_payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return db_payment


@transaction_router.post(
    "/settlement",
    response_model=ReferredTransactionSettlementResponseDTO,
    status_code=status.HTTP_201_CREATED
)
def create_settlement(
        payload: ReferredTransactionSettlementCreateDTO,
        current_user: Annotated[UserDTO, Depends(get_current_active_user)],
        repo: TransactionRepository = Depends(transaction_repo),
):
    settlement = repo.create_settlement(
        created_for=payload.created_for,
        commission=payload.commission,
        created_by=current_user.id,
        ref_transaction_ids=payload.transactions
    )
    return settlement


@transaction_router.get(
    "/settlement/",
    # response_model=List[ReferredTransactionSettlementResponseDTO],
    status_code=status.HTTP_200_OK
)
def get_settlement(
        current_user: Annotated[UserDTO, Depends(get_current_active_user)],
        limit: int = 0,
        skip: int = 0,
        start_date: str = '',
        last_date: str = '',
        referral_id: int = 0,
        search_text: str = '',
        repo: TransactionRepository = Depends(transaction_repo),
):
    return repo.get_settlement(
        limit=limit,
        skip=skip,
        start_date=start_date,
        last_date=last_date,
        referral_id=referral_id,
        search_text=search_text
    )


@transaction_router.put("/payments/{payment_id}", response_model=PaymentDTO)
def update_payment(payment_id: int,
                   payment: PaymentDTO,
                   db: Session = Depends(get_db),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    db_payment = transaction_repository.update_payment(db=db, payment_id=payment_id, payment=payment)
    if db_payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return db_payment


@transaction_router.delete("/payments")
def delete_payment(payment_id: int,
                   repo: PaymentRepository = Depends(payment_repo),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    payment = repo.delete_payment(payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@transaction_router.get("/payments/", tags=["Payment"])
def get_payments(limit: int = 15, skip: int = 0,
                 transaction_type: str = None,
                 client_id: int = 0, start_date: str = '', last_date: str = '', date_filter_status: str = '',
                 repo: PaymentRepository = Depends(payment_repo),*, 
    current_user: Annotated[UserDTO, Depends(get_current_active_user)]
):
    return repo.get_payments(limit, skip, transaction_type, client_id,
                             start_date, last_date)
