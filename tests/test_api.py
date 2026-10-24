from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.dependencies import get_db
from backend.main import create_app
from database.connection import Base
from services.auth_service import create_initial_admin


@pytest.fixture
def api_client(tmp_path) -> Iterator[TestClient]:
    engine = create_engine(f"sqlite:///{tmp_path / 'api-test.sqlite3'}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        create_initial_admin(session, "api-admin", "fictional-api-password")
        session.commit()

    app = create_app(initialize_on_startup=False)

    def override_get_db():
        with Session(engine) as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    engine.dispose()


def sign_in(client: TestClient, role: str = "admin") -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "api-admin", "password": "fictional-api-password"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == role
    assert "spms_session" in client.cookies


def test_health_and_cookie_authentication(api_client: TestClient) -> None:
    assert api_client.get("/api/health").json() == {"status": "ok"}
    assert api_client.get("/api/auth/me").status_code == 401

    sign_in(api_client)
    current = api_client.get("/api/auth/me")
    assert current.status_code == 200
    assert current.json()["username"] == "api-admin"

    assert api_client.post("/api/auth/logout").status_code == 204
    assert api_client.get("/api/auth/me").status_code == 401


def test_student_crud_and_archive(api_client: TestClient) -> None:
    sign_in(api_client)
    created = api_client.post(
        "/api/students",
        json={"register_number": "REG-API-1", "full_name": "Fictional API Student", "course": "Computer Engineering"},
    )
    assert created.status_code == 201, created.text
    student_id = created.json()["id"]
    assert api_client.get(f"/api/students/{student_id}").json()["register_number"] == "REG-API-1"

    duplicate = api_client.post(
        "/api/students",
        json={"register_number": "reg-api-1", "full_name": "Duplicate Student"},
    )
    assert duplicate.status_code == 409

    updated = api_client.put(
        f"/api/students/{student_id}",
        json={"register_number": "REG-API-1", "full_name": "Updated API Student", "course": "Computer Engineering"},
    )
    assert updated.status_code == 200
    assert updated.json()["full_name"] == "Updated API Student"

    archived = api_client.post(f"/api/students/{student_id}/archive")
    assert archived.status_code == 200
    assert archived.json()["archived"] is True
    assert api_client.get("/api/students").json() == []
    assert len(api_client.get("/api/students?include_archived=true").json()) == 1


def test_employee_crud_and_archive(api_client: TestClient) -> None:
    sign_in(api_client)
    created = api_client.post(
        "/api/employees",
        json={
            "employee_code": "EMP-API-1",
            "full_name": "Fictional API Employee",
            "department": "Engineering",
            "designation": "Instructor",
        },
    )
    assert created.status_code == 201, created.text
    employee_id = created.json()["id"]
    assert api_client.get(f"/api/employees/{employee_id}").status_code == 200

    updated = api_client.put(
        f"/api/employees/{employee_id}",
        json={
            "employee_code": "EMP-API-1",
            "full_name": "Updated API Employee",
            "department": "Engineering",
            "designation": "Senior Instructor",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["designation"] == "Senior Instructor"

    archived = api_client.post(f"/api/employees/{employee_id}/archive")
    assert archived.status_code == 200
    assert archived.json()["active"] is False
    assert api_client.get("/api/employees").json() == []


def test_teacher_can_manage_students_but_not_employees(api_client: TestClient) -> None:
    sign_in(api_client)
    created_user = api_client.post(
        "/api/users",
        json={
            "username": "api-teacher",
            "password": "fictional-teacher-password",
            "role": "teacher",
        },
    )
    assert created_user.status_code == 201, created_user.text
    api_client.post("/api/auth/logout")
    teacher_login = api_client.post(
        "/api/auth/login",
        json={"username": "api-teacher", "password": "fictional-teacher-password"},
    )
    assert teacher_login.status_code == 200

    student = api_client.post(
        "/api/students",
        json={"register_number": "TEACHER-1", "full_name": "Teacher Managed Student"},
    )
    assert student.status_code == 201
    assert api_client.post(
        "/api/employees",
        json={"employee_code": "TEACHER-EMP-1", "full_name": "No Access"},
    ).status_code == 403


def test_analytics_use_entered_marks_and_eligible_attendance(api_client: TestClient) -> None:
    sign_in(api_client)
    department = api_client.post("/api/departments", json={"code": "CE", "name": "Computer Engineering"})
    course = api_client.post(
        "/api/courses",
        json={"department_id": department.json()["id"], "code": "DCE", "name": "Diploma Computer Engineering"},
    )
    subject = api_client.post(
        "/api/subjects",
        json={"course_id": course.json()["id"], "code": "PY", "name": "Python Programming"},
    )
    examination = api_client.post(
        "/api/examinations",
        json={
            "subject_id": subject.json()["id"],
            "name": "Unit Test",
            "academic_year": "2026",
            "semester": "1",
            "maximum_marks": 100,
            "pass_marks": 40,
        },
    )
    student = api_client.post(
        "/api/students",
        json={"register_number": "ANALYTICS-1", "full_name": "Fictional Analytics Student"},
    )
    exam_id = examination.json()["id"]
    student_id = student.json()["id"]

    entered = api_client.post(
        "/api/marks",
        json={"examination_id": exam_id, "student_id": student_id, "status": "entered", "score": 75},
    )
    second_student = api_client.post(
        "/api/students",
        json={"register_number": "ANALYTICS-2", "full_name": "Fictional Missing Mark Student"},
    )
    pending = api_client.post(
        "/api/marks",
        json={"examination_id": exam_id, "student_id": second_student.json()["id"], "status": "absent"},
    )
    assert entered.status_code == 201, entered.text
    assert pending.status_code == 201, pending.text

    attendance = api_client.post(
        "/api/attendance/students",
        json={"student_id": student_id, "attendance_date": "2026-10-24", "status": "present"},
    )
    assert attendance.status_code == 201
    analytics = api_client.get("/api/analytics/academic").json()
    assert analytics["entered_mark_count"] == 1
    assert analytics["excluded_pending_or_absent"] == 1
    assert analytics["subject_averages"][0]["average_percentage"] == 75
    assert analytics["grade_distribution"]
    overview = api_client.get("/api/analytics/overview").json()
    assert overview["average_marks_percentage"] == 75
    assert overview["pass_percentage"] == 100
    assert overview["attendance_percentage"] == 100


def test_student_report_returns_database_csv(api_client: TestClient) -> None:
    sign_in(api_client)
    api_client.post(
        "/api/students",
        json={"register_number": "CSV-1", "full_name": "Fictional CSV Student"},
    )
    response = api_client.get("/api/reports/students.csv")
    assert response.status_code == 200
    assert "CSV-1" in response.text