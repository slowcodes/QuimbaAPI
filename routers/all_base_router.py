from routers.business_service_router import business_service_router
from routers.client.client_router import client_router
from routers.client.notification_router import notification_router
from routers.client.organisation_router import org_router
from routers.client.referral_router import referral_router
from routers.client.vital_router import vital_router
from routers.consultation_router import consultation_router
from routers.lab.lab_router import lab_router
from routers.lab.queue_router import queue_router
from routers.lab.result_router import result_router
from routers.lab.samples_router import sample_collection_router
from routers.product_router import product_router
from routers.security_router import security_router
from routers.service_router import service_router
from routers.supply_router import supply_router
from routers.transaction_router import transaction_router

base_routers = [
    product_router,
    transaction_router,
    supply_router,
    service_router,
    security_router,
    consultation_router,
    business_service_router,

    # client
    client_router,
    vital_router,
    org_router,
    notification_router,
    referral_router,

    lab_router,
    result_router,
    sample_collection_router,
    queue_router,
    service_router,
]