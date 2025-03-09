from passlib.context import CryptContext
import re

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def is_bcrypt_hash(hash_str):
    # Regex pattern for bcrypt hash
    bcrypt_pattern = r'^\$2[aby]?\$\d{2}\$[./A-Za-z0-9]{22}[./A-Za-z0-9]{31}$'

    # Check if the hash_str matches the bcrypt pattern
    if re.match(bcrypt_pattern, hash_str):
        return True
    return False
