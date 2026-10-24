from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database.models import Employee, Student
from services.auth_service import AuthenticatedUser, require_role


@dataclass(frozen=True)
class DashboardSummary:
    total_students: int | None
    total_employees: int | None


def get_dashboard_summary(session: Session, actor: AuthenticatedUser) -> DashboardSummary:
    require_role(actor, "admin", "teacher", "employee")
    if actor.role == "employee":
        return DashboardSummary(total_students=None, total_employees=None)

    total_students = session.scalar(
        select(func.count()).select_from(Student).where(Student.archived.is_(False))
    )
    total_employees = session.scalar(
        select(func.count()).select_from(Employee).where(Employee.active.is_(True))
    )
    return DashboardSummary(total_students=total_students or 0, total_employees=total_employees or 0)