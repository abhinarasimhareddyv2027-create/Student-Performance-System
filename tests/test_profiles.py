from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database.connection import Base, initialize_database
from database.models import Employee, Student, User
from services.auth_service import AuthenticatedUser
from services.employee_service import (
    EmployeeProfile,
    archive_employee,
    create_employee,
    get_employee,
    list_employees,
    update_employee,
)
from services.profile_common import DuplicateProfileError, ProfileValidationError
from services.student_service import (
    StudentProfile,
    archive_student,
    create_student,
    list_students,
    update_student,
)


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite://")
    initialize_database(engine)
    with Session(engine) as test_session:
        yield test_session
    engine.dispose()


@pytest.fixture
def admin() -> AuthenticatedUser:
    return AuthenticatedUser(1, "admin", "admin")


def test_student_create_search_filter_update_and_archive(
    session: Session, admin: AuthenticatedUser
) -> None:
    student = create_student(
        session,
        admin,
        StudentProfile(
            register_number=" R-100 ",
            full_name="Fictional Student",
            course="Diploma Computer Engineering",
            academic_year="2026",
            current_semester="3",
            email="student@example.test",
        ),
    )
    session.commit()

    assert student.register_number == "R-100"
    assert [item.id for item in list_students(session, admin, search="fictional", course="Diploma Computer Engineering")] == [student.id]

    updated = update_student(
        session,
        admin,
        student.id,
        StudentProfile(register_number="R-100", full_name="Updated Student", enrollment_status="graduated"),
    )
    session.commit()
    assert updated.full_name == "Updated Student"
    assert updated.enrollment_status == "graduated"

    archive_student(session, admin, student.id)
    session.commit()
    assert list_students(session, admin) == []
    assert len(list_students(session, admin, include_archived=True)) == 1


def test_student_duplicate_register_and_admission_numbers_rejected(
    session: Session, admin: AuthenticatedUser
) -> None:
    create_student(
        session,
        admin,
        StudentProfile(register_number="REG-1", full_name="First Student", admission_number="ADM-1"),
    )
    session.commit()

    with pytest.raises(DuplicateProfileError):
        create_student(session, admin, StudentProfile(register_number="reg-1", full_name="Second Student"))
    with pytest.raises(DuplicateProfileError):
        create_student(
            session,
            admin,
            StudentProfile(register_number="REG-2", full_name="Third Student", admission_number="ADM-1"),
        )


def test_student_fields_and_permissions_are_validated(session: Session, admin: AuthenticatedUser) -> None:
    with pytest.raises(ProfileValidationError, match="YYYY-MM-DD"):
        create_student(
            session,
            admin,
            StudentProfile(register_number="REG-1", full_name="Student", date_of_birth="yesterday"),
        )
    with pytest.raises(PermissionError):
        create_student(
            session,
            AuthenticatedUser(3, "employee", "employee"),
            StudentProfile(register_number="REG-1", full_name="Student"),
        )
    with pytest.raises(PermissionError):
        archive_student(session, AuthenticatedUser(2, "teacher", "teacher"), 1)


def test_employee_create_search_update_and_archive_disables_login(
    session: Session, admin: AuthenticatedUser
) -> None:
    employee = create_employee(
        session,
        admin,
        EmployeeProfile(
            employee_code="E-100",
            full_name="Fictional Employee",
            department="Engineering",
            designation="Instructor",
            joining_date="2024-06-01",
            work_email="employee@example.test",
        ),
    )
    employee.user = User(
        username="employee-login",
        password_hash="not-a-real-login-hash",
        role="employee",
    )
    session.commit()

    assert len(list_employees(session, admin, search="Fictional", department="Engineering")) == 1
    update_employee(
        session,
        admin,
        employee.id,
        EmployeeProfile(
            employee_code="E-100",
            full_name="Fictional Employee",
            department="Engineering",
            designation="Senior Instructor",
            employment_status="on_leave",
        ),
    )
    session.commit()
    assert employee.active is True
    assert employee.designation == "Senior Instructor"

    archive_employee(session, admin, employee.id)
    session.commit()
    assert employee.active is False
    assert employee.user.active is False
    assert list_employees(session, admin) == []


def test_employee_can_only_view_linked_profile(session: Session, admin: AuthenticatedUser) -> None:
    employee = create_employee(
        session,
        admin,
        EmployeeProfile(employee_code="E-1", full_name="Fictional Employee"),
    )
    other = create_employee(
        session,
        admin,
        EmployeeProfile(employee_code="E-2", full_name="Another Employee"),
    )
    session.commit()
    actor = AuthenticatedUser(9, "employee", "employee", employee_id=employee.id)

    assert get_employee(session, actor, employee.id).id == employee.id
    with pytest.raises(PermissionError):
        get_employee(session, actor, other.id)
    with pytest.raises(PermissionError):
        list_employees(session, actor)


def test_employee_profile_validation_and_duplicate_code(
    session: Session, admin: AuthenticatedUser
) -> None:
    with pytest.raises(ProfileValidationError, match="invalid"):
        create_employee(
            session,
            admin,
            EmployeeProfile(employee_code="E-1", full_name="Employee", work_email="bad-email"),
        )

    create_employee(session, admin, EmployeeProfile(employee_code="E-1", full_name="First Employee"))
    session.commit()
    with pytest.raises(DuplicateProfileError):
        create_employee(session, admin, EmployeeProfile(employee_code="E-1", full_name="Second Employee"))


def test_employee_profile_requires_admin_for_management(session: Session) -> None:
    teacher = AuthenticatedUser(2, "teacher", "teacher")
    with pytest.raises(PermissionError):
        list_employees(session, teacher)
    with pytest.raises(PermissionError):
        create_employee(session, teacher, EmployeeProfile(employee_code="E-1", full_name="Employee"))


def test_legacy_profile_schema_upgrade_preserves_records() -> None:
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE students (id INTEGER PRIMARY KEY, register_number VARCHAR(50) NOT NULL UNIQUE, "
            "full_name VARCHAR(160) NOT NULL, archived BOOLEAN NOT NULL DEFAULT 0)"
        )
        connection.exec_driver_sql(
            "CREATE TABLE employees (id INTEGER PRIMARY KEY, employee_code VARCHAR(50) NOT NULL UNIQUE, "
            "full_name VARCHAR(160) NOT NULL, department VARCHAR(120) NOT NULL DEFAULT '', "
            "designation VARCHAR(120) NOT NULL DEFAULT '', active BOOLEAN NOT NULL DEFAULT 1)"
        )
        connection.exec_driver_sql(
            "INSERT INTO students (register_number, full_name) VALUES ('OLD-1', 'Existing Student')"
        )
        connection.exec_driver_sql(
            "INSERT INTO employees (employee_code, full_name) VALUES ('OLD-E1', 'Existing Employee')"
        )

    initialize_database(engine)
    with Session(engine) as session:
        student = session.query(Student).filter_by(register_number="OLD-1").one()
        employee = session.query(Employee).filter_by(employee_code="OLD-E1").one()
        assert student.full_name == "Existing Student"
        assert student.admission_number is None
        assert employee.full_name == "Existing Employee"
        assert employee.work_email is None
    assert "admission_number" in {column["name"] for column in inspect(engine).get_columns("students")}
    engine.dispose()