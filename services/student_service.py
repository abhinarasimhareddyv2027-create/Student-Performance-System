from dataclasses import asdict, dataclass

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from database.models import Student
from services.auth_service import AuthenticatedUser, require_role
from services.profile_common import DuplicateProfileError, normalize_profile, save_profile


@dataclass(frozen=True)
class StudentProfile:
    register_number: str
    full_name: str
    admission_number: str | None = None
    date_of_birth: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    guardian_name: str | None = None
    guardian_contact: str | None = None
    course: str | None = None
    department: str | None = None
    branch: str | None = None
    academic_year: str | None = None
    current_semester: str | None = None
    section: str | None = None
    admission_date: str | None = None
    enrollment_status: str = "active"
    profile_image_path: str | None = None


def _profile_values(profile: StudentProfile) -> dict[str, object]:
    values = normalize_profile(asdict(profile), ("register_number", "full_name"))
    if values["enrollment_status"] not in {"active", "withdrawn", "graduated", "suspended", "archived"}:
        raise ValueError("Enrollment status is invalid.")
    return values


def create_student(session: Session, actor: AuthenticatedUser, profile: StudentProfile) -> Student:
    require_role(actor, "admin", "teacher")
    values = _profile_values(profile)
    instance = Student(**values)
    return save_profile(
        session,
        instance,
        or_(
            func.lower(Student.register_number) == values["register_number"].lower(),
            Student.admission_number == values["admission_number"]
            if values["admission_number"]
            else False,
        ),
        "Register or admission number is already in use.",
    )


def list_students(
    session: Session,
    actor: AuthenticatedUser,
    search: str = "",
    course: str | None = None,
    department: str | None = None,
    academic_year: str | None = None,
    semester: str | None = None,
    section: str | None = None,
    include_archived: bool = False,
) -> list[Student]:
    require_role(actor, "admin", "teacher")
    query = select(Student)
    if not include_archived:
        query = query.where(Student.archived.is_(False))
    if search.strip():
        pattern = f"%{search.strip()}%"
        query = query.where(or_(Student.full_name.ilike(pattern), Student.register_number.ilike(pattern)))
    for column, value in (
        (Student.course, course),
        (Student.department, department),
        (Student.academic_year, academic_year),
        (Student.current_semester, semester),
        (Student.section, section),
    ):
        if value:
            query = query.where(column == value.strip())
    return list(session.scalars(query.order_by(Student.full_name, Student.register_number)))


def get_student(session: Session, actor: AuthenticatedUser, student_id: int) -> Student | None:
    require_role(actor, "admin", "teacher")
    return session.get(Student, student_id)


def update_student(
    session: Session,
    actor: AuthenticatedUser,
    student_id: int,
    profile: StudentProfile,
) -> Student:
    require_role(actor, "admin", "teacher")
    student = session.get(Student, student_id)
    if student is None:
        raise LookupError("Student was not found.")
    values = _profile_values(profile)
    duplicate = session.scalar(
        select(Student.id).where(
            or_(
                func.lower(Student.register_number) == values["register_number"].lower(),
                Student.admission_number == values["admission_number"]
                if values["admission_number"]
                else False,
            ),
            Student.id != student_id,
        )
    )
    if duplicate:
        raise DuplicateProfileError("Register or admission number is already in use.")
    for key, value in values.items():
        setattr(student, key, value)
    session.flush()
    return student


def archive_student(session: Session, actor: AuthenticatedUser, student_id: int) -> Student:
    require_role(actor, "admin")
    student = session.get(Student, student_id)
    if student is None:
        raise LookupError("Student was not found.")
    student.archived = True
    student.enrollment_status = "archived"
    session.flush()
    return student