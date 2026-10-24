import os
import secrets
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt


JWT_SECRET = os.environ.get("SPS_JWT_SECRET_KEY") or secrets.token_urlsafe(48)
JWT_ALGORITHM = "HS256"
JWT_LIFETIME_MINUTES = 480
secure_default = "true" if os.environ.get("CODESPACES") == "true" else "false"
COOKIE_SECURE = os.environ.get("SPS_COOKIE_SECURE", secure_default).lower() == "true"


def create_access_token(user_id: int) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=JWT_LIFETIME_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": expires_at}, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return int(payload["sub"])
    except (JWTError, KeyError, TypeError, ValueError):
        return None