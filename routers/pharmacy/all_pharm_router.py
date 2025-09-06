from routers.pharmacy.drug_router import drug_router
from routers.pharmacy.pharmacy_router import pharmacy_router
from routers.pharmacy.prescription_router import prescription_router

pharm_routers = [
    pharmacy_router,
    drug_router,
    prescription_router
]