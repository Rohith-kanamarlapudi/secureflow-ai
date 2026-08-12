import jwt
import datetime

from app.core.config import settings


def create_access_token(sub: str) -> str:
    payload = {
        "sub": sub,
        "type": "access",
        "exp": datetime.datetime.utcnow()
        + datetime.timedelta(minutes=15),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm="HS256",
    )


def create_refresh_token(sub: str) -> str:
    payload = {
        "sub": sub,
        "type": "refresh",
        "exp": datetime.datetime.utcnow()
        + datetime.timedelta(days=7),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm="HS256",
    )