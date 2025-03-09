import logging

from fastapi import FastAPI
import uvicorn

from db import engine, Base
from routers import service_router, transaction_router, consultation_router, security_router
from routers.client import client_router
from routers.client import vital_router, nottification_router
from routers.lab import lab_router, queue_router, samples_router, result_router
import bootstrap.db_data_init
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

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

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(client_router.client_router)
app.include_router(lab_router.lab_router)
app.include_router(result_router.result_router)
app.include_router(samples_router.sample_collection_router)
app.include_router(queue_router.queue_router)
app.include_router(service_router.service_router)
app.include_router(transaction_router.transaction_router)
app.include_router(consultation_router.consultation_router)
app.include_router(security_router.security_router)
app.include_router(vital_router.vital_router)
app.include_router(nottification_router.notification_router)

# create tables
def create_table():
    Base.metadata.create_all(bind=engine)


create_table()
bootstrap.db_data_init.load_data()
logging.basicConfig(
    filename='app.log',  # File where logs will be written
    level=logging.ERROR,  # Log level threshold
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)
logging.error("This is an error message test")

if __name__ == '__main__':
    # Set up logging


    # SQLModel.metadata.create_all(engine)
    uvicorn.run('main:app', host="127.0.0.1", port=8001, reload=True)
