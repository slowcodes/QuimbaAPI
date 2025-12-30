# from repos.base_repository import BaseRepository
# from repos.consultation.consultant_repository import ConsultantRepository
# from repos.lab.lab_repository import LabRepository
# from repos.sale_repository import SaleRepository
# from repos.transaction_repository import TransactionRepository
#
#
# class SalesServiceRepository(BaseRepository):
#     def __init__(self, db):
#         super().__init__(db)
#         self.transaction_repository = TransactionRepository(db)
#         self.consultation_repository = ConsultantRepository(db)
#         self.laboratory_repository = LabRepository(db)
#         self.sales_repository = SaleRepository(db)
#
#     def get_full_transaction_details(self, transaction_id: int,
#                                      add_lab: bool = True,
#                                      add_consultation: bool = True,
#                                      add_sales: bool = True
#                                      ):
#         transaction_details = self.transaction_repository.get_transaction_by_id(
#             transaction_id)  # repo.get_laboratory_transaction(transaction_id)
#         lab_services = self.laboratory_repository.get_lab_services_booking(transaction_id)
#         consultation_services = self.consultation_repository.get_consultation_service_booking(transaction_id)
#         sales = self.sales_repository.get_by_transaction_id(transaction_id)
#
#         if transaction_details is not None:
#             transaction_details = transaction_details.dict()
#
#             all_service = lab_services + consultation_services
#
#             transaction_details['sales'] = sales if add_sales else []
#
#             transaction_details['lab_services'] = lab_services if add_lab else []
#             transaction_details['consultation_services'] = consultation_services if add_consultation else []
#             transaction_details['transaction_packages'] = self.transaction_repository.get_lab_transaction_packages(transaction_id) if add_sales else []
#             return transaction_details
#         return None
#
#     # def get_only_lab_trx_details(self, transaction_id: int):
#     #     transaction_details['lab'] = self.transaction_repository.get_all_lab()
#     #     transaction_details['consultation'] = self.transaction_repository.get_all_consultation()
#     #     transaction_details['dispensaries'] = self.transaction_repository.get_all_dispensaries()
#         transaction_details = self.transaction_repository.get_transaction_by_id(transaction_id)
