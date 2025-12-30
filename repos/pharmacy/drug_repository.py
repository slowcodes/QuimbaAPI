from typing import List, Optional

from sqlalchemy.orm import Session

from dtos.pharmacy.drug import DrugDTO, DrugInfoDTO, DrugGroupDTO, DrugFormDTO, PharmDrugPackageDTO
from dtos.product import ProductDTO
from models.pharmacy import Drug, DrugGroupTag, DrugGroup, DrugForm, PharmDrugFormPackage
from models.product import Product, ProductPackage, Barcode, PackageHierarchy
from models.sales import SalesPriceCode
from repos.base_repository import BaseRepository
from repos.product_repository import ProductRepository
from repos.sale_repository import SaleRepository


class DrugRepository(BaseRepository):

    def __init__(self, session: Session):
        self.session = session
        super().__init__(session)
        self.base_repository = BaseRepository(session)
        self.sales_repository = SaleRepository(session)
        self.product_repository = ProductRepository(session)

    def get(self, drug_id: int, include_deleted: bool = False) -> Optional[Drug]:
        query = self.session.query(Drug).filter(Drug.id == drug_id)
        if not include_deleted:
            query = query.filter(Drug.is_deleted == False)
        return self.get_complete_drug_dto(
            query.first())

    def get_drug_forms(self, drug_id: int):
        forms = self.session.query(DrugForm).filter(DrugForm.drug_id == drug_id).all()
        response = []
        for form in forms:
            # get packages associated to this form
            form_packages = self.session.query(PharmDrugFormPackage).filter(
                PharmDrugFormPackage.form_id == form.id).all()
            packs = []
            for pack in form_packages:
                spc = self.sales_repository.get_sales_code(pack.sales_price_code_id)

                packs.append(
                    PharmDrugPackageDTO(
                        id=pack.id,
                        form_id=pack.form_id,
                        sales_price_code=spc,
                        # parent_package_id=pack.parent_id,
                        package_container=pack.package_container,
                        product_barcode=self.product_repository.get_product_barcode_by_package_id(pack.id),
                    )
                )

            response.append(
                DrugFormDTO(
                    id=form.id,
                    drug_id=form.drug_id,
                    drug_form=form.drug_form,
                    form_packages=packs
                )
            )
        return response

    def get_all(self, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> List[Drug]:
        query = self.session.query(Drug)
        if not include_deleted:
            query = query.filter(Drug.is_deleted == False)
        count = query.count()
        drugs = query.offset(skip).limit(limit).all()

        res = []
        for drug in drugs:
            dg = self.get_complete_drug_dto(drug)

            res.append(
                dg
            )

        return res

    def get_complete_drug_dto(self, drug: Drug) -> DrugDTO:
        dg = DrugInfoDTO(**drug.__dict__)
        dg.drug_form = self.get_drug_forms(drug.id)
        product = ProductDTO.from_orm(self.product_repository.get(Product, drug.product_id))
        product.product_package = self.product_repository.get_product_package(drug.product_id)
        dg.drug_group = self.get_drug_groups(drug.id)

        return DrugDTO(
                    drug_info=dg,
                    product=product
                )

    def create(self, drug_data: DrugDTO) :
        try:
            product = drug_data.product.__dict__

            product.pop('product_package')
            product.pop('id')
            new_product = Product(**product)
            self.db.add(new_product)
            self.db.flush()

            drug = drug_data.drug_info.__dict__
            drug['product_id'] = new_product.id

            groups = drug.pop('drug_group')

            drug_form = drug.pop('drug_form')
            new_drug = Drug(**drug)
            self.db.add(new_drug)
            self.db.flush()

            for dg_form in drug_form:
                child = []
                parent = []

                dg_fm = DrugForm(
                        drug_form=dg_form.drug_form,
                        drug_id=new_drug.id
                    )
                self.db.add(dg_fm)
                self.db.flush()

                for fm_pkg in dg_form.form_packages:
                    # if fm_pkg.parent_package_id = 0, then it's a parent package else child
                    sales_price_code_data = fm_pkg.sales_price_code.__dict__
                    sales_price_code = SalesPriceCode(**sales_price_code_data)
                    self.add(sales_price_code)
                    self.db.flush()

                    drug_package = PharmDrugFormPackage(
                            form_id=dg_fm.id,
                            package_container=fm_pkg.package_container,
                            sales_price_code_id=sales_price_code.id,
                            # parent_package_id=form_package.parent_package_id
                        )
                    self.add(drug_package)
                    self.db.flush()

                    # if pack is child
                    if fm_pkg.parent_package_id != 0:
                        child.append({
                            'parent_package_id': fm_pkg.parent_package_id,  # temp parent_package_id
                            'package_id': drug_package.id,
                            'child_quantity_per_parent': fm_pkg.quantity_per_parent
                        })
                    else:
                        # pack is likely a parent
                        parent.append({
                            'tmp_parent_package_id': fm_pkg.id,
                            'package_id': drug_package.id,
                        })

                    barcodes = fm_pkg.product_barcode
                    for barcode in barcodes:
                        product_barcode = {
                            'barcode': barcode,
                            'product_packaging_id': drug_package.id
                        }
                        self.db.add(Barcode(**product_barcode))

                for child_pack in child:
                    # find the parent package id
                    parent_pack = next(
                        (p for p in parent if p['tmp_parent_package_id'] == child_pack['parent_package_id']),
                        None)
                    if parent_pack:
                        child_pack['parent_package_id'] = parent_pack['package_id']
                        # del child_pack['tmp_parent_package_id']
                        self.db.add(PackageHierarchy(**child_pack))

                for group in groups:
                    group_tag = {
                        'group_id': group.id,
                        'drug_id': new_drug.id
                    }
                    grp = DrugGroupTag(**group_tag)
                    self.db.add(grp)

            self.db.commit()
            return self.base_repository.get(Drug, new_drug.id)
        except Exception as e:
            self.session.rollback()
            raise e

    def update(self, drug_id: int, drug_data: DrugDTO) -> Optional[Drug]:
        db_drug = self.get(drug_id)
        if db_drug:
            for key, value in drug_data.dict(exclude_unset=True).items():
                setattr(db_drug, key, value)
            self.session.commit()
            self.session.refresh(db_drug)
        return db_drug

    # Soft delete specific operations

    def soft_delete(self, drug_id: int) -> Optional[Drug]:
        db_drug = self.get(drug_id)
        if db_drug:
            self.product_repository.soft_delete(db_drug.product_id)
            db_drug.delete()  # Using the mixin's delete method
            self.session.commit()
            self.session.refresh(db_drug)
        return db_drug

    def restore(self, drug_id: int) -> Optional[Drug]:
        db_drug = self.get(drug_id, include_deleted=True)
        if db_drug and db_drug.is_deleted:
            db_drug.restore()  # Using the mixin's restore method
            self.session.commit()
            self.session.refresh(db_drug)
        return db_drug

    # Additional useful queries

    def get_by_name(self, name: str, include_deleted: bool = False):
        products = self.product_repository.search_by_name(name)
        dg = []
        for product in products:
            query = self.session.query(Drug).filter(Drug.product_id == product.id)
            if not include_deleted:
                query = query.filter(Drug.is_deleted == False)
            drug = query.first()
            if drug:
                dg.append(
                    self.get_complete_drug_dto(drug)
                )
        return {'data': dg, 'count': len(products)}

    def get_by_manufacturer(self, manufacturer: str, include_deleted: bool = False) -> List[Drug]:
        query = self.session.query(Drug).filter(Drug.manufacturer.ilike(f"%{manufacturer}%"))
        if not include_deleted:
            query = query.filter(Drug.is_deleted == False)
        return query.all()

    def get_drug_groups(self, drug_id: int) -> List[DrugGroupDTO]:
        tags = self.session.query(DrugGroupTag).filter(DrugGroupTag.drug_id == drug_id).all()
        groups = []
        for tag in tags:
            group = self.session.query(DrugGroup).filter(DrugGroup.id == tag.group_id).first()
            if group:
                groups.append(DrugGroupDTO(**group.__dict__))
        return groups

    def get_deleted(self) -> List[Drug]:
        return self.session.query(Drug).filter(Drug.is_deleted == True).all()
