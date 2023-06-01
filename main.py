from fastapi import FastAPI
import uvicorn
from fastapi.params import Depends
from sqlalchemy.orm import Session
from db import engine, Base, create_engine, SessionLocal
from models.client import State
from routers import client_router, lab_router
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


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(client_router.client_router)
app.include_router(lab_router.lab_router)


# create tables
def create_table():
    Base.metadata.create_all(bind=engine)


create_table()
bootstrap.db_data_init.load_data()

if __name__ == '__main__':
    # SQLModel.metadata.create_all(engine)
    uvicorn.run('main:app', host="127.0.0.1", port=8001, reload=True)
