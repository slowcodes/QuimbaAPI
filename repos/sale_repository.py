from typing import Optional, List

from dtos.sales import SalesPriceCodeDTO, BusinessSalesRead
from models.sales import SalesPriceCode, BusinessSales
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

    def create(self, data: dict) -> BusinessSales:
        """Create a new BusinessSales record."""
        sale = BusinessSales(**data)
        self.db.add(sale)
        self.db.commit()
        self.db.refresh(sale)
        return sale

    def get_by_id(self, sale_id: int) -> Optional[BusinessSalesRead]:
        """Retrieve a sale by its ID."""
        return self.db.query(BusinessSales).filter(BusinessSales.id == sale_id).first()

    def get_by_transaction_id(self, transaction_id: int) -> List[BusinessSalesRead]:
        """Retrieve a sale by its ID."""
        sales = self.db.query(BusinessSales).filter(BusinessSales.transaction_id == transaction_id).all()
        return [BusinessSalesRead.from_orm(sale) for sale in sales] if sales else []

    def list(self, skip: int = 0, limit: int = 100) -> List[BusinessSales]:
        """List sales with pagination."""
        return (
            self.db.query(BusinessSales)
            .offset(skip)
            .limit(limit)
            .all()
        )

