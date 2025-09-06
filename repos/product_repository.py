from typing import List, Optional

from dtos.product import ProductPackageDTO
from dtos.sales import SalesPriceCodeDTO
from models.product import Product, Barcode, ProductPackage
from models.sales import SalesPriceCode
from repos.base_repository import BaseRepository


class ProductRepository(BaseRepository):

    def search_by_name(self, product_name: str):
        return self.db.query(Product).filter(
            Product.brand_name.ilike(f'%{product_name}%')
        ).all()

    def get_by_name(self, product_name: str):
        return self.db.query(Product).filter(Product.product_name == product_name).first()

    def list_by_manufacturer(self, manufacturer: str):
        return self.db.query(Product).filter(Product.manufacturer == manufacturer).all()

    def get_product_barcode(self, product_packaging_id: int) -> List[str]:
        barcodes = self.db.query(Barcode).filter(Barcode.product_packaging_id == product_packaging_id).all()

        codes = []
        for barcode in barcodes:
            codes.append(barcode.barcode)
        return codes

    def soft_delete(self, drug_id: int) -> Optional[Product]:
        db_drug = self.get(Product, drug_id)
        if db_drug:
            db_drug.delete()  # Using the mixin's delete method
            self.db.commit()
            self.db.refresh(db_drug)
        return db_drug

    def get_product_barcode_by_package_id(self, package_id: int) -> List[str]:
        barcodes = self.db.query(Barcode).filter(Barcode.product_packaging_id == package_id).all()

        codes = []
        for barcode in barcodes:
            codes.append(barcode.barcode)
        return codes


    def get_product_hierarchy(self, package_id: int):
        return False

    def get_product_package(self, product_id: int) -> List[ProductPackageDTO]:
        product_packages = self.db.query(ProductPackage).filter(ProductPackage.product_id == product_id).all()

        pp = []
        for product_package in product_packages:
            pack = product_package.__dict__
            barcode = self.get_product_barcode(pack['id'])
            sales_price_code = SalesPriceCodeDTO.from_orm(
                self.db.query(SalesPriceCode).filter(SalesPriceCode.id == product_package.sales_price_code_id).first()
            )

            pack['sales_price_code'] = sales_price_code
            pack['product_barcode'] = barcode
            pp.append(ProductPackageDTO(**pack))

        return pp
