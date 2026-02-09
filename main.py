import logging
from datetime import datetime

from fastapi import FastAPI, Request
import uvicorn
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from db import engine, Base
import bootstrap.db_data_init
from fastapi.middleware.cors import CORSMiddleware

from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse
from routers.pharmacy.all_pharm_router import pharm_routers
from routers.all_base_router import base_routers
from routers.sales.all import sales_router
import os

import redis

from security.dependencies import refresh_access_token


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
    expose_headers=["X-Refresh-Token"],
)


@app.middleware("http")
async def sliding_jwt_refresh(request: Request, call_next):
    response = await call_next(request)

    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[len("Bearer "):].strip()
        new_token = refresh_access_token(token)
        if new_token:
            response.headers["X-Refresh-Token"] = new_token

    return response


for route in pharm_routers:
    app.include_router(route, prefix='')

for route in sales_router:
    app.include_router(route, prefix='')

for route in base_routers:
    app.include_router(route, prefix='')


if os.getenv("AUTO_CREATE_TABLES", "false").lower() == "true":
    Base.metadata.create_all(bind=engine)
    bootstrap.db_data_init.load_pg_data()

logging.basicConfig(
    filename='app.log',  # File where logs will be written
    level=logging.ERROR,  # Log level threshold
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
logging.error("App has re-started. Startup time: "+current_time)

if __name__ == '__main__':
    # Set up logging

    # SQLModel.metadata.create_all(engine)
    uvicorn.run('main:app', host="0.0.0.0", port=8000, reload=True, workers=5)
