from io import StringIO

import pandas as pd
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.dependencies import get_db, require_roles
from database.models import Employee, Student
from services.auth_service import AuthenticatedUser


router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/students.csv")
def export_students(
    actor: AuthenticatedUser = Depends(require_roles("admin", "teacher")),
    session: Session = Depends(get_db),
) -> StreamingResponse:
    students = session.scalars(select(Student).where(Student.archived.is_(False)).order_by(Student.register_number))
    frame = pd.DataFrame(
        [
            {
                "register_number": row.register_number,
                "admission_number": row.admission_number,
                "full_name": row.full_name,
                "course": row.course,
                "department": row.department,
                "academic_year": row.academic_year,
                "semester": row.current_semester,
                "section": row.section,
                "status": row.enrollment_status,
            }
            for row in students
        ]
    )
    output = StringIO()
    frame.to_csv(output, index=False)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=students.csv"},
    )


@router.get("/employees.csv")
def export_employees(
    actor: AuthenticatedUser = Depends(require_roles("admin")),
    session: Session = Depends(get_db),
) -> StreamingResponse:
    employees = session.scalars(select(Employee).where(Employee.active.is_(True)).order_by(Employee.employee_code))
    frame = pd.DataFrame(
        [
            {
                "employee_code": row.employee_code,
                "full_name": row.full_name,
                "department": row.department,
                "designation": row.designation,
                "work_email": row.work_email,
                "work_phone": row.work_phone,
                "employment_status": row.employment_status,
            }
            for row in employees
        ]
    )
    output = StringIO()
    frame.to_csv(output, index=False)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=employees.csv"},
    )