import logging
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os


# Configure SQLAlchemy logger
# logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# SQLALCHEMY_DATABASE_URL = "sqlite:///./Quimba.db"
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
# SQLALCHEMY_DATABASE_URL = 'mysql+pymysql://root:password123@db:3306/Quimba'

# SQLite Specific
# engine = create_engine(
#     SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
# )

# Docker MySQL User: Quimba, Password:password123

# MySQL and Postgress
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

session = SessionLocal()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
