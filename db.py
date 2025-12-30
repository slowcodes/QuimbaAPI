import logging
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL") + "?options=-csearch_path=public"
# engine = create_engine(
#     SQLALCHEMY_DATABASE_URL, echo=False
# )
#
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()
# session = SessionLocal()
#
#

DATABASE_URL = os.environ["DATABASE_URL"] + "?options=-csearch_path=public"

# ONE metadata
metadata = MetaData()

# ONE base
Base = declarative_base(metadata=metadata)

engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
