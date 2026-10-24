from dataclasses import dataclass

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database.models import User


PASSWORD_HASHER = PasswordHasher()
VALID_ROLES = frozenset({"admin", "teacher", "employee"})


class AuthenticationError(ValueError):
    """Raised when account setup or authentication input is invalid."""


@dataclass(frozen=True)
class AuthenticatedUser:
    id: int
    username: str
    role: str
    employee_id: int | None = None


def hash_password(password: str) -> str:
    if len(password) < 12:
        raise AuthenticationError("Password must contain at least 12 characters.")
    return PASSWORD_HASHER.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return PASSWORD_HASHER.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def create_initial_admin(session: Session, username: str, password: str) -> User:
    normalized_username = username.strip()
    if not normalized_username or len(normalized_username) > 80:
        raise AuthenticationError("Username must contain 1 to 80 characters.")
    password_hash = hash_password(password)
    if session.scalar(select(func.count()).select_from(User)):
        raise AuthenticationError("Initial admin setup is only available for an empty user store.")

    user = User(
        username=normalized_username,
        password_hash=password_hash,
        role="admin",
    )
    session.add(user)
    try:
        session.flush()
    except IntegrityError as error:
        session.rollback()
        raise AuthenticationError("Could not create the initial admin account.") from error
    return user


def authenticate_user(session: Session, username: str, password: str) -> AuthenticatedUser | None:
    user = session.scalar(select(User).where(User.username == username.strip()))
    if user is None or not user.active or not verify_password(user.password_hash, password):
        return None

    if PASSWORD_HASHER.check_needs_rehash(user.password_hash):
        user.password_hash = PASSWORD_HASHER.hash(password)
        session.flush()
    return AuthenticatedUser(
        id=user.id,
        username=user.username,
        role=user.role,
        employee_id=user.employee_id,
    )


def require_role(actor: AuthenticatedUser, *allowed_roles: str) -> None:
    if actor.role not in VALID_ROLES or actor.role not in allowed_roles:
        raise PermissionError("You are not authorized to perform this action.")