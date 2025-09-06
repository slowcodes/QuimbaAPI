from dtos.sales import SalesPriceCodeDTO
from models.sales import SalesPriceCode
from repos.base_repository import BaseRepository


class SaleRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db)

    def get_sales_code(self, id: int):
        sales_code = self.get(SalesPriceCode, id)
        return SalesPriceCodeDTO(
            id=sales_code.id,
            selling_price=sales_code.selling_price,
            buying_price=sales_code.buying_price
        )
