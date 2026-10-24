from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.dependencies import get_db, require_roles
from backend.audit import record_audit
from backend.schemas import UserCreateInput, UserView
from database.academic_models import AuditEvent
from database.models import Employee, User
from services.auth_service import AuthenticatedUser, hash_password


router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserView])
def list_users(
    actor: AuthenticatedUser = Depends(require_roles("admin")),
    session: Session = Depends(get_db),
) -> list[User]:
    return list(session.scalars(select(User).order_by(User.username)))


@router.post("", response_model=UserView, status_code=201)
def create_user(
    payload: UserCreateInput,
    actor: AuthenticatedUser = Depends(require_roles("admin")),
    session: Session = Depends(get_db),
) -> User:
    username = payload.username.strip()
    if not username:
        raise HTTPException(status_code=422, detail="Username is required.")
    if payload.employee_id is not None:
        employee = session.get(Employee, payload.employee_id)
        if employee is None or not employee.active:
            raise HTTPException(status_code=422, detail="An active employee profile is required.")
    user = User(
        username=username,
        password_hash=hash_password(payload.password),
        role=payload.role,
        employee_id=payload.employee_id,
    )
    session.add(user)
    try:
        session.flush()
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(status_code=409, detail="Username or employee account is already in use.") from error
    record_audit(session, actor, "create", "user", user.id)
    return user


@router.patch("/{user_id}/active", response_model=UserView)
def set_user_active(
    user_id: int,
    active: bool,
    actor: AuthenticatedUser = Depends(require_roles("admin")),
    session: Session = Depends(get_db),
) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.id == actor.id and not active:
        raise HTTPException(status_code=422, detail="You cannot deactivate your own account.")
    user.active = active
    record_audit(session, actor, "activate" if active else "deactivate", "user", user.id)
    return user