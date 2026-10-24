from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database.connection import Base
from services.auth_service import (
    AuthenticationError,
    AuthenticatedUser,
    authenticate_user,
    create_initial_admin,
    require_role,
    verify_password,
)


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as test_session:
        yield test_session
    engine.dispose()


def test_initial_admin_password_is_hashed_and_authenticates(session: Session) -> None:
    admin = create_initial_admin(session, "  campus-admin  ", "a-long-test-password")
    session.commit()

    assert admin.username == "campus-admin"
    assert admin.password_hash != "a-long-test-password"
    assert verify_password(admin.password_hash, "a-long-test-password")
    actor = authenticate_user(session, "CAMPUS-ADMIN", "a-long-test-password")
    assert actor is not None and actor.role == "admin"


def test_initial_admin_cannot_be_recreated(session: Session) -> None:
    create_initial_admin(session, "admin", "a-long-test-password")
    session.commit()

    with pytest.raises(AuthenticationError, match="empty user store"):
        create_initial_admin(session, "another-admin", "another-long-password")


def test_bad_credentials_return_no_user(session: Session) -> None:
    create_initial_admin(session, "admin", "a-long-test-password")
    session.commit()

    assert authenticate_user(session, "admin", "incorrect-password") is None
    assert authenticate_user(session, "missing", "incorrect-password") is None


def test_password_minimum_length_is_enforced() -> None:
    with pytest.raises(AuthenticationError, match="12 characters"):
        create_initial_admin(Session(), "admin", "short")


def test_role_permissions_are_checked() -> None:
    require_role(AuthenticatedUser(1, "teacher", "teacher"), "teacher", "admin")
    with pytest.raises(PermissionError):
        require_role(AuthenticatedUser(2, "employee", "employee"), "admin")