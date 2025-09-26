from sqlalchemy.orm import Session

from dtos.lab import DateFilterDTO
from dtos.transaction import TransactionDTO, TransactionPackageDTO
from models.auth import User
from models.client import Person, Client
from models.services.services import ServiceBooking, BookingStatus, Bundles
from models.transaction import Transaction, TransactionType, ReferredTransaction, PackageTransaction
from repos.auth_repository import UserRepository
from repos.client.client_repository import ClientRepository
from repos.client.referral_repository import ReferralRepository
from repos.consultation.consultant_repository import ConsultantRepository
from repos.lab.lab_repository import LabRepository
from repos.payment_repository import PaymentRepository
from repos.services.service_bundle_repository import ServiceBundleRepository
from repos.services.service_repository import ServiceRepository
from utils.functions import generate_transaction_id


class TransactionRepository:

    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.user_id = 1  # getLoggedInUser()['id']
        self.result_cols = [
            Transaction.id,
            Transaction.transaction_time,
            Transaction.discount,
            Transaction.user_id,
            Person.last_name,
            Person.first_name,
            ServiceBooking.client_id,
            # Client.id.label("client_id"),
            ServiceBooking.booking_status,
            ServiceBooking.id.label("booking_id")
        ]
        self.service_repository = ServiceRepository(self.db_session)
        self.service_bundle_repository = ServiceBundleRepository(self.db_session)
        self.referral_repository = ReferralRepository(self.db_session)

    def get_transactions(self, limit, skip, lab_id,
                         booking_status: BookingStatus, search_text: str, transaction_type: TransactionType,
                         client_id: int, date_filter: DateFilterDTO, booking_id: int = 0,
                         only_referred_transaction: bool = False):

        rs = self.db_session.query(*self.result_cols).select_from(ServiceBooking) \
            .join(Transaction, Transaction.id == ServiceBooking.transaction_id) \
            .join(Client, Client.id == ServiceBooking.client_id) \
            .join(Person, Person.id == Client.person_id)

        if only_referred_transaction:
            rs = rs.join(ReferredTransaction, ReferredTransaction.transaction_id == Transaction.id)

        if transaction_type != TransactionType.All:
            rs = rs.filter(Transaction.transaction_status == transaction_type)

        if booking_status:
            rs = rs.filter(ServiceBooking.booking_status == booking_status)

        if booking_id != 0:
            rs = rs.filter(ServiceBooking.id == booking_id)

        if date_filter.get("start_date") or date_filter.get("last_date"):
            start_date = date_filter.get("start_date")
            last_date = date_filter.get("last_date") + ' 23:59:59.999999'
            rs = rs.filter(
                Transaction.transaction_time.between(start_date, last_date)
                if start_date and last_date else
                Transaction.transaction_time >= start_date if start_date else
                Transaction.transaction_time <= last_date
            )

        if client_id != 0:
            rs = rs.filter(Client.id == client_id)

        if len(search_text) > 2:
            rs = rs.where((Person.first_name.ilike(f"%{search_text}%")) |
                          (Person.last_name.ilike(f"%{search_text}%")) |
                          (Person.phone.ilike(f"%{search_text}%"))
                          )

        total = rs.count()
        transactions = rs.order_by(Transaction.transaction_time.desc()).offset(skip).limit(limit).all()
        return {
            'transactions': transactions,
            'total': total
        }

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

    def get_laboratory_transaction(self, transaction_id):

        rs = self.db_session.query(*self.result_cols) \
            .select_from(Transaction) \
            .join(User, User.id == Transaction.user_id) \
            .join(Person, User.person_id == Person.id) \
            .join(ServiceBooking, ServiceBooking.transaction_id == Transaction.id) \
            .filter(Transaction.id == transaction_id).one_or_none()

        if rs is None:
            return None

        client = ClientRepository(self.db_session)
        payments = PaymentRepository(self.db_session)

        user = UserRepository(self.db_session)

        userWithOutPerson = user.get_user_by_id(rs.user_id)
        userWithPerson = user.get_user(userWithOutPerson.username)

        client = client.get_client(rs.client_id)
        transaction_date = str(rs.transaction_time)
        return {
            'transaction_id': rs.id,
            'discount': rs.discount,
            'processed_by': rs.first_name + ' ' + rs.last_name,
            'client': client,
            'user': userWithPerson,
            'transaction_package': self.get_lab_transaction_packages(transaction_id),
            'client_first_name': client['first_name'],
            'client_last_name': client['last_name'],
            'booking_status': rs.booking_status,
            'transaction_time': transaction_date,
            'payment': payments.get_transaction_payments(transaction_id),
            # 'services': lab.get_lab_services_booking(transaction_id)
        }

    def get_laboratory_transaction_details(self, limit, skip, lab_id,
                                           booking_status: BookingStatus, search_text: str,
                                           client_id: int, date_filter: DateFilterDTO,
                                           transaction_type: TransactionType, only_referred_transactions: bool = False):
        rs = self.get_transactions(limit, skip, lab_id,
                                   booking_status, search_text, transaction_type,
                                   client_id, date_filter, 0, only_referred_transactions)

        prp = PaymentRepository(self.db_session)
        urp = UserRepository(self.db_session)
        lrp = LabRepository(self.db_session)

        response = []
        for lab_booking in rs['transactions']:
            payments = prp.get_transaction_payments(lab_booking.id)
            user = urp.get_user_by_id(lab_booking.user_id)
            lab_services = lrp.get_lab_services_booking(lab_booking.id)
            response.append(
                {
                    'transaction_id': lab_booking.id,
                    'transaction_time': lab_booking.transaction_time,
                    'status': lab_booking.booking_status,
                    'client_first_name': lab_booking.first_name,
                    'client_last_name': lab_booking.last_name,
                    'discount': lab_booking.discount,
                    'service_agent': user,
                    'teller': urp.get_user(user.username),
                    'booking_completion_status': self.service_repository.get_booking_completion_status(
                        lab_booking.booking_id),
                    'payment': payments,
                    'services': lab_services,
                    'referral': self.referral_repository.get_referred_transaction_referral(lab_booking.id)
                }
            )
        return {
            'data': response,
            'total': rs['total']
        }

    def tid_exist(self, tid: int) -> bool:
        exits = self.db_session.query(Transaction).filter(Transaction.id == tid)
        if exits is not None:
            return True
        return False

    def create_transaction(self, discount: float):
        tid = generate_transaction_id()

        continue_tid_generation = True
        while continue_tid_generation:
            continue_tid_generation = not self.tid_exist(tid)

        new_transaction = Transaction(id=tid, user_id=self.user_id, discount=discount)
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
        return self.db_session.query(Transaction).filter(Transaction.id == transaction_id).first()

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
        cols = [
            Client.person_id,
            Client.address,
            Person.first_name,
            Person.last_name,
            Client.id
        ]
        lab_repository = LabRepository(self.db_session)
        consultation_repository = ConsultantRepository(self.db_session)

        clients_with_open_transactions = self.db_session.query(*cols) \
            .select_from(Client) \
            .join(ServiceBooking, ServiceBooking.client_id == Client.id) \
            .join(Transaction, Transaction.id == ServiceBooking.transaction_id) \
            .join(Person, Person.id == Client.person_id) \
            .distinct() \
            .filter(Transaction.transaction_status == 'Open') \
            .offset(skip).limit(limit).all()

        result = []
        for client in clients_with_open_transactions:
            open_transactions = self.db_session.query(Transaction) \
                .join(ServiceBooking, ServiceBooking.transaction_id == Transaction.id) \
                .filter(ServiceBooking.client_id == client.id,
                        Transaction.transaction_status == TransactionType.Open
                        ).all()

            transaction = []
            for txn in open_transactions:
                transaction.append(
                    {
                        'id': txn.id,
                        'discount': txn.discount,
                        'transaction_time': txn.transaction_time,
                        'details': lab_repository.get_lab_services_booking(txn) + consultation_repository.get_consultation_service_booking(txn)
                    }
                )

            result.append({
                'client_id': client.id,
                'first_name': client.first_name,
                'last_name': client.last_name,
                'open_transactions': transaction
            })

        return result
