from sqlalchemy.orm import Session

from dtos.services import PriceCodeDTO
from models.services.services import PriceCode


class PriceRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, price: PriceCodeDTO) -> PriceCodeDTO:
        db_price = PriceCode(**price.dict())
        self.session.add(db_price)
        self.session.commit()
        self.session.refresh(db_price)
        return PriceCodeDTO(**db_price.__dict__)

    def get_price_code_by_id(self, id:int)-> PriceCodeDTO:
        price_code = self.session.query(PriceCode).filter(PriceCode.id == id).one_or_none()

        if price_code:
            return PriceCodeDTO(**price_code.__dict__)
        return None
