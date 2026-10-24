from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from database.connection import Base
from services.auth_service import create_initial_admin
from ui.console import run_console


@pytest.fixture
def session_factory() -> Iterator[sessionmaker[Session]]:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        create_initial_admin(session, "console-admin", "fictional-test-password")
        session.commit()
    yield factory
    engine.dispose()


def test_console_dashboard_authenticates_and_shows_real_counts(
    session_factory: sessionmaker[Session],
) -> None:
    output: list[str] = []

    result = run_console(
        session_factory,
        username_reader=lambda _prompt: "console-admin",
        password_reader=lambda _prompt: "fictional-test-password",
        output=output.append,
    )

    assert result == 0
    assert "Students: 0" in output
    assert "Employees: 0" in output
    assert any("read-only" in line for line in output)


def test_console_rejects_bad_credentials(session_factory: sessionmaker[Session]) -> None:
    output: list[str] = []

    result = run_console(
        session_factory,
        username_reader=lambda _prompt: "console-admin",
        password_reader=lambda _prompt: "wrong-password",
        output=output.append,
    )

    assert result == 1
    assert any("Sign-in failed" in line for line in output)