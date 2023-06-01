from fastapi import FastAPI
import uvicorn
from fastapi.params import Depends
from sqlalchemy.orm import Session
from db import engine, Base, create_engine, SessionLocal
from models.people import State
from routers import client_router
import bootstrap.db_data_init

app = FastAPI()

app = FastAPI(
    title="Quimba API",
    description="This API and it's accompanying documentation is developed and maintained by Business Innovation and Techonology Systems. Its provides details on how to access the identity and and biometric enrollment services provided by the DataTruck Platform.",
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


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app.include_router(client_router.client_router)


# create tables
Base.metadata.create_all(bind=engine)
bootstrap.db_data_init.load_data()

if __name__ == '__main__':
    # SQLModel.metadata.create_all(engine)
    uvicorn.run('main:app', host="127.0.0.1", port=8001, reload=True)
