from datetime import datetime
import random

def date_formatter(date_str: str) -> str:
    return datetime.strptime(date_str, '%a %b %d %Y %H:%M:%S GMT%z (%Z)')


def generate_transaction_id() -> int:
    return random.randint(100000000000, 999999999999)


def sqlalchemy_to_dict(obj):
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
