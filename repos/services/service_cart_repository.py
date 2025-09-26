from select import select
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session

from dtos.service_dtos.client_cart_service import ClientServiceCartDTO, ClientServiceCartPackageDTO, \
    ClientServiceCartDetailDTO
from models.services.service_cart import ClientServiceCart, ClientServiceCartPackage, ClientServiceCartDetail


class ServiceCartRepository:
    def __init__(self, db: Session):
        self.db = db

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