import traceback

from sqlalchemy import select
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session

from dtos.service_dtos.client_cart_service import ClientServiceCartDTO, ClientServiceCartPackageDTO, \
    ClientServiceCartDetailDTO, ProcessedCartDTO
from models.services.service_cart import ClientServiceCart, ClientServiceCartPackage, ClientServiceCartDetail
from models.services.services import BookingType, BookingStatus
from repos.lab.lab_repository import LabRepository


class ServiceCartRepository:
    def __init__(self, db: Session):
        self.db = db
        self.lab_repository = LabRepository(db)

    def get_client_carts(self, client_id: int = 0, limit: int = 20, skip: int = 0) -> list[ClientServiceCartDTO]:
        """
        Fetches a list of service carts for a specific client with pagination.
        """
        try:
            query = self.db.query(ClientServiceCart)  # Ensure the model is registered
            if client_id:
                query = query.filter(ClientServiceCart.client_id == client_id)
            carts = query.offset(skip).limit(limit).all()
            client_cart = [ClientServiceCartDTO.from_orm(cart) for cart in carts]

            for cart_item in client_cart:
                service_cart_details = []
                for service_item in cart_item.client_service_cart_details:
                    if service_item.service_type == BookingType.Appointment:
                        service_item.service_desc = "Medical Appointment"
                        service_item.appointment_data = service_item.client_consultation_booking_carts
                    elif service_item.service_type == BookingType.Laboratory:
                        lab = self.lab_repository.get_lab_service_details_by_service_id(service_item.service_id)
                        service_item.service_desc = lab

                    service_cart_details.append(service_item)
                cart_item.client_service_cart_details = service_cart_details

            return client_cart
        except SQLAlchemyError as e:
            print(f"Database error while fetching client carts: {e}")
            raise e
        except Exception as e:
            traceback.print_exc()
            print(f"Unexpected error while fetching client carts: {e}")
            raise e

    def get_client_service_cart_dto(self, client_id: int) -> Optional[ClientServiceCartDTO]:
        """
        Fetches the latest (most recently created) service cart for a client and returns it as a DTO.
        """
        try:
            stmt = (
                select(ClientServiceCart)
                .where(ClientServiceCart.client_id == client_id)
                .order_by(ClientServiceCart.created_at.desc())
                .limit(1)
            )
            cart: Optional[ClientServiceCart] = self.db.exec(stmt).first()
            if not cart:
                return None

            # Fetch related packages and details
            packages = self.db.exec(
                select(ClientServiceCartPackage).where(ClientServiceCartPackage.cart_id == cart.id)
            ).all()
            details = self.db.exec(
                select(ClientServiceCartDetail).where(ClientServiceCartDetail.cart_id == cart.id)
            ).all()

            # Convert to DTOs
            packages_dto = [ClientServiceCartPackageDTO.from_orm(pkg) for pkg in packages]
            details_dto = [ClientServiceCartDetailDTO.from_orm(det) for det in details]

            cart_dto = ClientServiceCartDTO.from_orm(cart)
            cart_dto.client_service_cart_packages = packages_dto
            cart_dto.client_service_cart_details = details_dto

            return cart_dto

        except SQLAlchemyError as e:
            print(f"Database error while fetching client service cart DTO: {e}")
            raise e
        except Exception as e:
            print(f"Unexpected error while fetching client service cart DTO: {e}")
            raise e

    def get_client_service_cart_by_transaction_id(self, transaction_id: int) -> Optional[ClientServiceCartDTO]:
        """
        Fetches the service cart associated with a specific transaction ID and returns it as a DTO.
        """
        try:
            stmt = (
                select(ClientServiceCart)
                .where(ClientServiceCart.transaction_id == transaction_id)
                .order_by(ClientServiceCart.created_at.desc())
                .limit(1)
            )

            cart: Optional[ClientServiceCart] = self.db.execute(stmt).scalars().first()
            if not cart:
                return None

            # Fetch related packages and details
            packages = self.db.execute(
                select(ClientServiceCartPackage).where(ClientServiceCartPackage.cart_id == cart.id)
            ).scalars().all()

            details = self.db.execute(
                select(ClientServiceCartDetail).where(ClientServiceCartDetail.cart_id == cart.id)
            ).scalars().all()

            # Convert to DTOs
            packages_dto = [ClientServiceCartPackageDTO.from_orm(pkg) for pkg in packages]
            details_dto = [ClientServiceCartDetailDTO.from_orm(det) for det in details]

            cart_dto = ClientServiceCartDTO.from_orm(cart)
            cart_dto.client_service_cart_packages = packages_dto
            cart_dto.client_service_cart_details = details_dto

            return cart_dto

        except SQLAlchemyError as e:
            print(f"Database error while fetching client service cart by transaction ID: {e}")
            raise e
        except Exception as e:
            print(f"Unexpected error while fetching client service cart by transaction ID: {e}")
            raise e

    def update_cart_status(self, cart_status: ProcessedCartDTO) -> Optional[ProcessedCartDTO]:
        cart = self.db.query(ClientServiceCart)\
            .filter((ClientServiceCart.id == cart_status.cart_id) &
                    (ClientServiceCart.client_id == cart_status.client_id)).first()
        if not cart:
            return None
        counter = 0;
        for in_service in cart.client_service_cart_details:

            for service_id in cart_status.processed_services:
                if in_service.service_id == service_id:
                    counter += 1
                    in_service.processing_status = BookingStatus.Processed
                    # self.db.add(in_service)
        if counter == len(cart.client_service_cart_details):
            cart.cart_status = BookingStatus.Processed
            # self.db.add(cart)
        self.db.commit()
        return cart_status

    def create_client_service_cart(self, cart_dto: ClientServiceCartDTO) -> ClientServiceCart:
        """
        Accepts a ClientServiceCartDTO, saves it (and its nested packages/details) into the DB.
        Returns the persisted ClientServiceCart object.
        """
        try:
            # Create main cart
            cart = ClientServiceCart(
                client_id=cart_dto.client_id,
                cart_status=cart_dto.cart_status,
                referral_id=cart_dto.referral_id,
                transaction_id=cart_dto.transaction_id,
                created_by=cart_dto.created_by
            )

            self.db.add(cart)
            self.db.flush()  # assign cart.id

            # Add packages
            for pkg in cart_dto.client_service_cart_packages:
                package = ClientServiceCartPackage(
                    package_id=pkg.package_id,
                    cart_id=cart.id
                )
                self.db.add(package)

            # Add details
            for detail in cart_dto.client_service_cart_details:
                detail_obj = ClientServiceCartDetail(
                    price_code_id=detail.price_code_id,
                    service_id=detail.service_id,
                    service_type=detail.service_type,
                    cart_id=cart.id
                )
                self.db.add(detail_obj)
                self.db.flush()

                if detail.appointment_data and detail.appointment_data.consultant_id:
                    # Assuming AppointmentData has a method to convert to ORM model
                    appointment = detail.appointment_data.to_orm_model()
                    appointment.cart_detail_id = detail_obj.id
                    self.db.add(appointment)

            self.db.commit()
            self.db.refresh(cart)
            return cart

        except SQLAlchemyError as e:
            self.db.rollback()
            # optional: log error here
            print(f"Database error while creating client service cart: {e}")
            raise e

        except Exception as e:
            self.db.rollback()
            # optional: log error here
            print(f"Unexpected error while creating client service cart: {e}")
            raise e
