from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database.connection import Base
from database.models import Employee, Student
from services.auth_service import AuthenticatedUser
from services.dashboard_service import get_dashboard_summary


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as test_session:
        yield test_session
    engine.dispose()


def test_summary_counts_only_active_records(session: Session) -> None:
    session.add_all(
        [
            Student(register_number="R-1", full_name="Fictional Student"),
            Student(register_number="R-2", full_name="Archived Student", archived=True),
            Employee(employee_code="E-1", full_name="Fictional Employee"),
            Employee(employee_code="E-2", full_name="Inactive Employee", active=False),
        ]
    )
    session.flush()
    summary = get_dashboard_summary(session, AuthenticatedUser(1, "teacher", "teacher"))

    assert summary.total_students == 1
    assert summary.total_employees == 1


def test_unknown_role_cannot_read_dashboard(session: Session) -> None:
    with pytest.raises(PermissionError):
        get_dashboard_summary(session, AuthenticatedUser(1, "unknown", "unknown"))


def test_employee_does_not_see_institution_wide_counts(session: Session) -> None:
    session.add(Student(register_number="R-1", full_name="Fictional Student"))
    session.flush()

    summary = get_dashboard_summary(session, AuthenticatedUser(3, "employee", "employee"))

    assert summary.total_students is None
    assert summary.total_employees is None