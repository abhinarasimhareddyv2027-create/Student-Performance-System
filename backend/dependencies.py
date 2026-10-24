from collections.abc import Iterator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from database.connection import SessionLocal
from database.models import User
from services.auth_service import AuthenticatedUser
from backend.security import decode_access_token


def get_db() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_current_actor(request: Request, session: Session = Depends(get_db)) -> AuthenticatedUser:
    token = request.cookies.get("spms_session")
    user_id = decode_access_token(token) if token else None
    user = session.get(User, user_id) if user_id is not None else None
    if user is None or not user.active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    return AuthenticatedUser(user.id, user.username, user.role, user.employee_id)


def require_roles(*roles: str):
    def dependency(actor: AuthenticatedUser = Depends(get_current_actor)) -> AuthenticatedUser:
        if actor.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized.")
        return actor

    return dependency