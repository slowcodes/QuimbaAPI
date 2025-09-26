import logging

from fastapi import FastAPI, Request
import uvicorn
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from db import engine, Base
from routers import supply_router, service_router, transaction_router, consultation_router, security_router
from routers.client import organisation_router, client_router, referral_router
from routers.client import vital_router, notification_router
from routers.lab import lab_router, queue_router, samples_router, result_router
import bootstrap.db_data_init
from fastapi.middleware.cors import CORSMiddleware

from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse
import redis

from routers.pharmacy.all_pharm_router import pharm_routers

app = FastAPI(default_response_class=ORJSONResponse)
app.add_middleware(GZipMiddleware, minimum_size=1000)


app = FastAPI(
    title="Quimba API",
    description="This API and it's accompanying documentation is developed and maintained by Business Innovation and Techonology Systems. Its provides details on how to access the identity and and biometric enrollment services.py provided by the DataTruck Platform.",
    version="0.0.1",
    terms_of_service="https://bitsystems.com.ng/terms/",
    contact={
        "name": "Business Innovation & Technology",
        "url": "https://bitsystems.com.ng/contact/",
        "email": "dp@bitsystems.com.ng",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)

r = redis.Redis(host="localhost", port=6379, db=0)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define the custom exception handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


origins = [
    "http://webapp",  # Use the container name instead of localhost
    "http://webapp:80",  # Angular runs on port 80 inside its container
    "http://localhost",  # If deployed
    "http://127.0.0.1",
]
origins = ['*']
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(client_router.client_router)
app.include_router(organisation_router.org_router)
app.include_router(lab_router.lab_router)
app.include_router(supply_router.supply_router)
app.include_router(result_router.result_router)
app.include_router(samples_router.sample_collection_router)
app.include_router(queue_router.queue_router)
app.include_router(service_router.service_router)
app.include_router(transaction_router.transaction_router)
app.include_router(consultation_router.consultation_router)
app.include_router(security_router.security_router)
app.include_router(vital_router.vital_router)
app.include_router(notification_router.notification_router)
app.include_router(referral_router.referral_router)

for route in pharm_routers:
    app.include_router(route, prefix='')


# @app.on_event("startup")
# async def on_startup():
#     run_migrations()


# create tables
def create_table():
    Base.metadata.create_all(bind=engine)


create_table()
bootstrap.db_data_init.load_pg_data()
logging.basicConfig(
    filename='app.log',  # File where logs will be written
    level=logging.ERROR,  # Log level threshold
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)
logging.error("This is an error message test")

if __name__ == '__main__':
    # Set up logging

    # SQLModel.metadata.create_all(engine)
    uvicorn.run('main:app', host="0.0.0.0", port=8000, reload=True, workers=5)
