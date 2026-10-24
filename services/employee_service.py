from dataclasses import asdict, dataclass

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from database.models import Employee
from services.auth_service import AuthenticatedUser, require_role
from services.profile_common import DuplicateProfileError, normalize_profile, save_profile


@dataclass(frozen=True)
class EmployeeProfile:
    employee_code: str
    full_name: str
    department: str = ""
    designation: str = ""
    work_email: str | None = None
    work_phone: str | None = None
    joining_date: str | None = None
    employment_status: str = "active"
    reporting_manager: str | None = None
    emergency_contact: str | None = None
    skills: str | None = None
    certifications: str | None = None
    profile_image_path: str | None = None


EMPLOYMENT_STATUSES = {"active", "on_leave", "inactive", "terminated", "archived"}


def _profile_values(profile: EmployeeProfile) -> dict[str, object]:
    values = normalize_profile(asdict(profile), ("employee_code", "full_name"))
    if values["employment_status"] not in EMPLOYMENT_STATUSES:
        raise ValueError("Employment status is invalid.")
    values["active"] = values["employment_status"] in {"active", "on_leave"}
    return values


def create_employee(session: Session, actor: AuthenticatedUser, profile: EmployeeProfile) -> Employee:
    require_role(actor, "admin")
    values = _profile_values(profile)
    instance = Employee(**values)
    return save_profile(
        session,
        instance,
        Employee.employee_code == values["employee_code"],
        "Employee code is already in use.",
    )


def list_employees(
    session: Session,
    actor: AuthenticatedUser,
    search: str = "",
    department: str | None = None,
    designation: str | None = None,
    include_inactive: bool = False,
) -> list[Employee]:
    require_role(actor, "admin")
    query = select(Employee)
    if not include_inactive:
        query = query.where(Employee.active.is_(True))
    if search.strip():
        pattern = f"%{search.strip()}%"
        query = query.where(or_(Employee.full_name.ilike(pattern), Employee.employee_code.ilike(pattern)))
    if department:
        query = query.where(Employee.department == department.strip())
    if designation:
        query = query.where(Employee.designation == designation.strip())
    return list(session.scalars(query.order_by(Employee.full_name, Employee.employee_code)))


def get_employee(session: Session, actor: AuthenticatedUser, employee_id: int) -> Employee | None:
    if actor.role == "admin":
        return session.get(Employee, employee_id)
    if actor.role == "employee" and actor.employee_id == employee_id:
        return session.get(Employee, employee_id)
    raise PermissionError("You are not authorized to view this employee profile.")


def update_employee(
    session: Session,
    actor: AuthenticatedUser,
    employee_id: int,
    profile: EmployeeProfile,
) -> Employee:
    require_role(actor, "admin")
    employee = session.get(Employee, employee_id)
    if employee is None:
        raise LookupError("Employee was not found.")
    values = _profile_values(profile)
    duplicate = session.scalar(
        select(Employee.id).where(
            Employee.employee_code == values["employee_code"],
            Employee.id != employee_id,
        )
    )
    if duplicate:
        raise DuplicateProfileError("Employee code is already in use.")
    for key, value in values.items():
        setattr(employee, key, value)
    session.flush()
    return employee


def archive_employee(session: Session, actor: AuthenticatedUser, employee_id: int) -> Employee:
    require_role(actor, "admin")
    employee = session.get(Employee, employee_id)
    if employee is None:
        raise LookupError("Employee was not found.")
    employee.active = False
    employee.employment_status = "archived"
    if employee.user is not None:
        employee.user.active = False
    session.flush()
    return employee