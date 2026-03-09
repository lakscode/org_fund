from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.config import config
from app.models import find_user_by_id
from app.logger import get_logger

logger = get_logger("auth")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password):
    logger.info("Hashing password")
    return pwd_context.hash(password)


def verify_password(plain, hashed):
    logger.info("Verifying password")
    result = pwd_context.verify(plain, hashed)
    if result:
        logger.info("Password verification succeeded")
    else:
        logger.info("Password verification failed")
    return result


def create_access_token(data, expires_delta=None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    logger.info("Creating access token for sub=%s, expires=%s", data.get("sub"), expire.isoformat())
    token = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    logger.info("Access token created successfully")
    return token


def get_current_user(token):
    logger.info("Decoding access token")
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            logger.error("Token payload missing 'sub' claim")
            return None
    except jwt.ExpiredSignatureError:
        logger.error("Token has expired")
        return None
    except jwt.PyJWTError as e:
        logger.error("Token decode failed: %s", e, exc_info=True)
        return None
    logger.info("Token valid, fetching user id=%s", user_id)
    user = find_user_by_id(user_id)
    if not user:
        logger.error("User not found for token sub=%s", user_id)
    return user
