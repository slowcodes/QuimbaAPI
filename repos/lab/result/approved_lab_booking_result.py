from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from dtos.auth import UserDTO
from models.lab.lab import ApprovedLabBookingResult
from dtos.lab import ApprovedLabBookingResultDTO
from typing import Optional

from repos.auth_repository import UserRepository


class ApprovedLabBookingResultRepository:
    def __init__(self, db: Session):

        self.db = db

    def get_by_id(self, id: int) -> Optional[ApprovedLabBookingResultDTO]:
        result = self.db.query(ApprovedLabBookingResult).filter(ApprovedLabBookingResult.id == id).first()
        if result:
            return ApprovedLabBookingResultDTO.from_orm(result)
        return None

    def get_by_booking_id(self, booking_id: int) -> Optional[ApprovedLabBookingResultDTO]:
        user_repo = UserRepository(self.db)
        result = self.db.query(ApprovedLabBookingResult).filter(
            ApprovedLabBookingResult.booking_id == booking_id).first()

        if result:
            # user = user_repo.get_user_by_id(result.approved_by)
            response = ApprovedLabBookingResultDTO.from_orm(result)
            response.approved_user = user_repo.get_usr_by_id(result.approved_by)
            return response
        return None

    def create(self, dto: ApprovedLabBookingResultDTO, user: UserDTO) -> ApprovedLabBookingResultDTO:
        try:
            # if booking has been approved, do nothing
            approval = self.get_by_booking_id(dto.booking_id)

            if approval:
                return approval

            dto.approved_by = user.id
            dto_dict = dto.dict()

            print('approval detail', dto_dict)
            filtered_data = {k: v for k, v in dto_dict.items() if v is not None and k != "approved_user"}

            data = ApprovedLabBookingResult(**filtered_data)
            self.db.add(data)
            self.db.commit()
            self.db.refresh(data)
            return ApprovedLabBookingResultDTO.from_orm(data)
        except SQLAlchemyError as e:
            print(f"An error occurred: {e}")
            return None

    def update(self, id: int, dto: ApprovedLabBookingResultDTO) -> Optional[ApprovedLabBookingResultDTO]:
        try:
            result = self.db.query(ApprovedLabBookingResult).filter(ApprovedLabBookingResult.id == id).first()
            if result:
                for key, value in dto.dict(exclude_unset=True).items():
                    setattr(result, key, value)
                self.db.commit()
                self.db.refresh(result)
                return ApprovedLabBookingResultDTO.from_orm(result)
            return None
        except SQLAlchemyError as e:
            print(f"An error occurred: {e}")
            return None

    def delete_by_booking_id(self, id: int) -> bool:
        try:
            result = self.db.query(ApprovedLabBookingResult).filter(ApprovedLabBookingResult.booking_id == id).delete()
            self.db.commit()
            return result > 0
        except SQLAlchemyError as e:
            print(f"An error occurred: {e}")
            return False
