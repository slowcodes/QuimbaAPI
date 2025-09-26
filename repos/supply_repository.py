from typing import List

from sqlalchemy import func

from dtos.pharmacy.drug import DrugDTO
from dtos.supply import SupplyDTO
from models.pharmacy import Drug, DrugForm, PharmacyDrugMovement, PharmDrugFormPackage
from models.product import ProductPackage
from models.supply import Supply, SupplyDetail, SupplyPharmDetail
from models.transaction import Payments
from repos.base_repository import BaseRepository
from repos.pharmacy.drug_repository import DrugRepository
from repos.transaction_repository import TransactionRepository


class SupplyRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db)
        self.transaction_repository = TransactionRepository(db)
        self.drug_repository = DrugRepository(db)

    def process_supply(self, supply: SupplyDTO):
        try:
            transaction = self.transaction_repository.create_transaction(supply.discount)

            supply_data = self.add(
                Supply(
                    transaction_id=transaction["id"],
                    supplier_id=supply.supplier.supplier_id,
                    pharmacy_id=supply.pharmacy.id
                )
            )

            for product in supply.cart:
                self.add(
                    SupplyDetail(
                        product_id=product.drug.product.id,
                        manufacture_date=product.manufacture_date,
                        expiry_date=product.expiry_date,
                        # drug_form=product.drug_form,
                        quantity=product.supply_quantity,
                        product_packaging_id=product.package_container,
                        supply_id=supply_data.id,
                    )
                )

                # record drug movement
                self.add(
                    PharmacyDrugMovement(
                        transaction_id=transaction["id"],
                        drug_form=product.drug_form,
                        drug_id=product.drug.drug_info.id,
                        package_type=product.package_container,
                        quantity=-product.supply_quantity,
                    )
                )

                self.add(
                    SupplyPharmDetail(
                        supply_id=supply_data.id,
                        drug_form=product.drug_form
                    )
                )

            # process payment
            for pay in supply.payment:
                self.add(
                    Payments(
                        amount=pay.amount,
                        transaction_id=transaction["id"],
                        user_id=transaction["user_id"],
                        payment_method=pay.payment_method
                    )
                )

            # If you have a commit method, call it here:
            self.commit_transaction()  # <-- commit all changes here

            return supply

        except Exception as e:
            # If you have a rollback method, call it here:
            self.rollback_transaction()  # <-- rollback changes on failure
            # log or re-raise the exception for the caller
            raise e

    def commit_transaction(self):
        self.db.commit()

    def rollback_transaction(self):
        self.db.rollback()

    def pharmacy_inventory(self, skip: int = 0, limit: int = 100, include_deleted: bool = False,
                           pharm_id: int = 0) -> List:
        drugs = self.drug_repository.get_all(skip, limit)

        stock = []
        for drug in drugs:
            count = {
                "stock": self.stock_in_pharmacy(drug)
            }
            stock.append(drug.__dict__ | count)
        return stock

    def stock_in_pharmacy(self, drug: DrugDTO) -> int:

        drug_forms = self.db.query(DrugForm).filter(DrugForm.drug_id == drug.drug_info.id).all()

        stock = []
        for drug_form in drug_forms:
            # get all packages of this form
            drug_form_packages = self.db.query(PharmDrugFormPackage).filter(PharmDrugFormPackage.form_id == drug_form.id).all()

            for drug_form_package in drug_form_packages:
                quantity = self.db.query(func.sum(PharmacyDrugMovement.quantity)) \
                               .filter(
                    PharmacyDrugMovement.drug_id == drug.drug_info.id,
                    PharmacyDrugMovement.package_type == drug_form_package.id
                ).scalar() or 0

                stock.append({
                    'form': drug_form.drug_form,
                    'quantity': quantity,
                    'package': drug_form_package.__dict__,
                })

        return stock
