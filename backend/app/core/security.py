from datetime import UTC, datetime, timedelta
from hashlib import sha256

import bcrypt
from jose import jwt

from app.core.config import settings

ALG = "HS256"


def _digest(value: str) -> bytes:
    return sha256(value.encode("utf-8")).hexdigest().encode("ascii")


def hash_password(value: str) -> str:
    return bcrypt.hashpw(_digest(value), bcrypt.gensalt()).decode("utf-8")


def verify_password(value: str, hashed: str) -> bool:
    return bcrypt.checkpw(_digest(value), hashed.encode("utf-8"))


def create_access_token(user_id: str, org_id: str, role: str) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user_id),
            "org": str(org_id),
            "org_id": str(org_id),
            "role": role,
            "iat": now,
            "exp": now + timedelta(minutes=settings.access_token_minutes),
        },
        settings.secret_key,
        algorithm=ALG,
    )


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[ALG])


def hash_token(token: str) -> str:
    return sha256(token.encode()).hexdigest()


create_token = create_access_token
