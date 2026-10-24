from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.dependencies import get_current_actor, get_db, require_roles
from backend.audit import record_audit
from backend.schemas import EmployeeInput, EmployeeView, StudentInput, StudentView
from database.models import Employee, Student
from services.auth_service import AuthenticatedUser
from services.employee_service import (
    EmployeeProfile,
    archive_employee,
    create_employee,
    get_employee,
    list_employees,
    update_employee,
)
from services.profile_common import DuplicateProfileError
from services.student_service import (
    StudentProfile,
    archive_student,
    create_student,
    get_student,
    list_students,
    update_student,
)


router = APIRouter(tags=["profiles"])


def _translate_profile_error(error: Exception) -> HTTPException:
    if isinstance(error, DuplicateProfileError):
        return HTTPException(status_code=409, detail=str(error))
    if isinstance(error, PermissionError):
        return HTTPException(status_code=403, detail=str(error))
    if isinstance(error, LookupError):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(error, ValueError):
        return HTTPException(status_code=422, detail=str(error))
    return HTTPException(status_code=500, detail="Profile operation failed.")


@router.get("/students", response_model=list[StudentView])
def students(
    search: str = "",
    course: str | None = None,
    department: str | None = None,
    academic_year: str | None = None,
    semester: str | None = None,
    section: str | None = None,
    include_archived: bool = False,
    actor: AuthenticatedUser = Depends(require_roles("admin", "teacher")),
    session: Session = Depends(get_db),
) -> list[Student]:
    try:
        return list_students(
            session,
            actor,
            search,
            course,
            department,
            academic_year,
            semester,
            section,
            include_archived,
        )
    except (PermissionError, ValueError) as error:
        raise _translate_profile_error(error) from error


@router.post("/students", response_model=StudentView, status_code=201)
def create_student_record(
    payload: StudentInput,
    actor: AuthenticatedUser = Depends(require_roles("admin", "teacher")),
    session: Session = Depends(get_db),
) -> Student:
    try:
        student = create_student(session, actor, StudentProfile(**payload.model_dump()))
        record_audit(session, actor, "create", "student", student.id)
        return student
    except (PermissionError, ValueError) as error:
        raise _translate_profile_error(error) from error


@router.get("/students/{student_id}", response_model=StudentView)
def student_detail(
    student_id: int,
    actor: AuthenticatedUser = Depends(require_roles("admin", "teacher")),
    session: Session = Depends(get_db),
) -> Student:
    student = get_student(session, actor, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student was not found.")
    return student


@router.put("/students/{student_id}", response_model=StudentView)
def edit_student(
    student_id: int,
    payload: StudentInput,
    actor: AuthenticatedUser = Depends(require_roles("admin", "teacher")),
    session: Session = Depends(get_db),
) -> Student:
    try:
        student = update_student(session, actor, student_id, StudentProfile(**payload.model_dump()))
        record_audit(session, actor, "update", "student", student.id)
        return student
    except (PermissionError, ValueError, LookupError) as error:
        raise _translate_profile_error(error) from error


@router.post("/students/{student_id}/archive", response_model=StudentView)
def archive_student_record(
    student_id: int,
    actor: AuthenticatedUser = Depends(require_roles("admin")),
    session: Session = Depends(get_db),
) -> Student:
    try:
        student = archive_student(session, actor, student_id)
        record_audit(session, actor, "archive", "student", student.id)
        return student
    except (PermissionError, LookupError) as error:
        raise _translate_profile_error(error) from error


@router.get("/employees", response_model=list[EmployeeView])
def employees(
    search: str = "",
    department: str | None = None,
    designation: str | None = None,
    include_inactive: bool = False,
    actor: AuthenticatedUser = Depends(require_roles("admin")),
    session: Session = Depends(get_db),
) -> list[Employee]:
    return list_employees(session, actor, search, department, designation, include_inactive)


@router.get("/employees/me", response_model=EmployeeView)
def my_employee_profile(
    actor: AuthenticatedUser = Depends(get_current_actor),
    session: Session = Depends(get_db),
) -> Employee:
    if actor.role == "employee" and actor.employee_id is not None:
        employee = get_employee(session, actor, actor.employee_id)
        if employee is not None:
            return employee
    raise HTTPException(status_code=404, detail="Linked employee profile was not found.")


@router.post("/employees", response_model=EmployeeView, status_code=201)
def create_employee_record(
    payload: EmployeeInput,
    actor: AuthenticatedUser = Depends(require_roles("admin")),
    session: Session = Depends(get_db),
) -> Employee:
    try:
        employee = create_employee(session, actor, EmployeeProfile(**payload.model_dump()))
        record_audit(session, actor, "create", "employee", employee.id)
        return employee
    except (PermissionError, ValueError) as error:
        raise _translate_profile_error(error) from error


@router.get("/employees/{employee_id}", response_model=EmployeeView)
def employee_detail(
    employee_id: int,
    actor: AuthenticatedUser = Depends(get_current_actor),
    session: Session = Depends(get_db),
) -> Employee:
    try:
        employee = get_employee(session, actor, employee_id)
    except PermissionError as error:
        raise _translate_profile_error(error) from error
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee was not found.")
    return employee


@router.put("/employees/{employee_id}", response_model=EmployeeView)
def edit_employee(
    employee_id: int,
    payload: EmployeeInput,
    actor: AuthenticatedUser = Depends(require_roles("admin")),
    session: Session = Depends(get_db),
) -> Employee:
    try:
        employee = update_employee(session, actor, employee_id, EmployeeProfile(**payload.model_dump()))
        record_audit(session, actor, "update", "employee", employee.id)
        return employee
    except (PermissionError, ValueError, LookupError) as error:
        raise _translate_profile_error(error) from error


@router.post("/employees/{employee_id}/archive", response_model=EmployeeView)
def archive_employee_record(
    employee_id: int,
    actor: AuthenticatedUser = Depends(require_roles("admin")),
    session: Session = Depends(get_db),
) -> Employee:
    try:
        employee = archive_employee(session, actor, employee_id)
        record_audit(session, actor, "archive", "employee", employee.id)
        return employee
    except (PermissionError, LookupError) as error:
        raise _translate_profile_error(error) from error