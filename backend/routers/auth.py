from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.dependencies import get_current_actor, get_db
from backend.schemas import LoginInput, UserView
from backend.security import COOKIE_SECURE, JWT_LIFETIME_MINUTES, create_access_token
from database.models import User
from services.auth_service import AuthenticatedUser, authenticate_user


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=UserView)
def login(payload: LoginInput, response: Response, session: Session = Depends(get_db)) -> User:
    actor = authenticate_user(session, payload.username, payload.password)
    if actor is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")
    user = session.get(User, actor.id)
    token = create_access_token(actor.id)
    response.set_cookie(
        "spms_session",
        token,
        max_age=JWT_LIFETIME_MINUTES * 60,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/",
    )
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> Response:
    response.delete_cookie("spms_session", path="/")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserView)
def current_user(
    actor: AuthenticatedUser = Depends(get_current_actor),
    session: Session = Depends(get_db),
) -> User:
    return session.get(User, actor.id)