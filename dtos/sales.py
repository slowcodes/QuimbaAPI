from typing import Optional

from pydantic import BaseModel


class SalesPriceCodeDTO(BaseModel):
    id: Optional[int] = None
    selling_price: Optional[float] = None
    buying_price: Optional[float] = None

    class Config:
        from_attributes = True
