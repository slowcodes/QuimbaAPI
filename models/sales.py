from sqlalchemy import Boolean, Column, ForeignKey, Integer, Double, String, DateTime, Date, Enum as SqlEnum, Text, BLOB
from db import Base



class BusinessSales(Base):
    __tablename__ = "Sales"

    id = Column(Integer, primary_key=True, index=True)
    price_code = Column(String(30))
    transaction_id = (Integer, ForeignKey("transaction.id", ondelete='CASCADE'))


class PriceCode(Base):
    __tablename__ = "Sales_Price_Code"

    id = Column(Integer, primary_key=True, index=True)
    selling_price = Column(Double)
    buying_price = Column(Double)
    discount = Column(Double)


class Product(Base):
    __tablename__ = "Products"

    id = Column(Integer, primary_key=True, index=True)
    current_price = Column(Double)
    name = Column(String(100))
    description = Column(String(100))


class Barcode(Base):
    __tablename__ = "Product_Barcode"

    id = Column(Integer, primary_key=True, index=True)
    barcode = Column(String(100))
    product_id = (Integer, ForeignKey("product.id", ondelete='CASCADE'))
