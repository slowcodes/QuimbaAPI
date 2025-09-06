from enum import Enum

from sqlalchemy import Enum as SqlEnum, Column, Integer, String, ForeignKey, Index, Double, Date
from sqlalchemy.orm import relationship
from db import Base
from models.mixins import SoftDeleteMixin


class Product(Base, SoftDeleteMixin):
    __tablename__ = "product"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # price_code = Column(Integer, ForeignKey("sales_price_code.id", ))  # Price of the drug
    brand_name = Column(String(100))
    product_name = Column(String(100))
    product_desc = Column(String(100))
    manufacturer = Column(String(100))  # Manufacturer of the drug

    pharmacy_drug = relationship("Drug", back_populates="product")  # Use string reference

    __table_args__ = (
        Index('ix_product_name', 'product_desc'),
        Index('ix_brand_name', 'brand_name'),
    )


class PackagingType(str, Enum):
    Cartoon = 'Cartoon'
    Card = 'Card'
    Tablet = 'Tablet'
    Pack = 'Pack'
    Capsule = 'Capsule'
    Can = 'Can'
    Bottle = 'Bottle'
    Patch = 'Patch'


# Not to be used drugs
class ProductPackage(Base, SoftDeleteMixin):
    __tablename__ = "product_package"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("product.id", ondelete="cascade"))
    package_container = Column(SqlEnum(PackagingType))
    sales_price_code_id = Column(Integer, ForeignKey("sales_price_code.id", ondelete="cascade"))

    # barcode = relationship("Barcode", back_populates="product_packaging")
    sales_price_code = relationship("SalesPriceCode", back_populates="product_package")
    sales = relationship("BusinessSales", back_populates="product_package")


class PackageHierarchy(Base, SoftDeleteMixin):
    __tablename__ = "product_packaging_hierarchy"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    parent_package_id = Column(Integer, ForeignKey("pharmacy_drug_form_package.id", ondelete="cascade"))
    package_id = Column(Integer, ForeignKey("pharmacy_drug_form_package.id", ondelete="cascade"))
    child_quantity_per_parent = Column(Double)


class Barcode(Base, SoftDeleteMixin):
    __tablename__ = "product_barcode"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    barcode = Column(String(100))
    product_packaging_id = Column(Integer, ForeignKey("pharmacy_drug_form_package.id", ondelete="cascade" ))  # FIXED

    pharmacy_drug_form_package = relationship("PharmDrugFormPackage", back_populates="product_barcode")
