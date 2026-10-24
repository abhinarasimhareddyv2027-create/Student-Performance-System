from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.audit import record_audit
from backend.dependencies import get_current_actor, get_db, require_roles
from backend.schemas import (
    ActivityInput,
    ActivityView,
    CourseInput,
    CourseView,
    DepartmentInput,
    DepartmentView,
    EmployeeAttendanceInput,
    EmployeeAttendanceView,
    ExaminationInput,
    ExaminationView,
    LeaveInput,
    LeaveView,
    MarkInput,
    MarkView,
    ReviewInput,
    ReviewView,
    StudentAttendanceInput,
    StudentAttendanceView,
    SubjectInput,
    SubjectView,
    TaskInput,
    TaskView,
)
from database.academic_models import (
    Activity,
    Course,
    Department,
    EmployeeAttendance,
    EmployeeTask,
    Examination,
    LeaveRequest,
    Mark,
    PerformanceReview,
    StudentAttendance,
    Subject,
)
from database.models import Employee, Student
from services.auth_service import AuthenticatedUser


router = APIRouter(tags=["academics and operations"])


def _save(session: Session, actor: AuthenticatedUser, instance: object, entity: str):
    session.add(instance)
    try:
        session.flush()
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(status_code=409, detail="Duplicate or invalid related record.") from error
    record_audit(session, actor, "create", entity, getattr(instance, "id", None))
    return instance


def _date(value: str, label: str) -> str:
    try:
        date.fromisoformat(value)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=f"{label} must use YYYY-MM-DD.") from error
    return value


@router.get("/departments", response_model=list[DepartmentView])
def departments(
    include_archived: bool = False,
    actor: AuthenticatedUser = Depends(require_roles("admin", "teacher")),
    session: Session = Depends(get_db),
) -> list[Department]:
    query = select(Department)
    if not include_archived:
        query = query.where(Department.archived.is_(False))
    return list(session.scalars(query.order_by(Department.name)))


@router.post("/departments", response_model=DepartmentView, status_code=201)
def create_department(
    payload: DepartmentInput,
    actor: AuthenticatedUser = Depends(require_roles("admin")),
    session: Session = Depends(get_db),
) -> Department:
    return _save(
        session,
        actor,
        Department(code=payload.code.strip(), name=payload.name.strip()),
        "department",
    )


@router.put("/departments/{department_id}", response_model=DepartmentView)
def update_department(
    department_id: int,
    payload: DepartmentInput,
    actor: AuthenticatedUser = Depends(require_roles("admin")),
    session: Session = Depends(get_db),
) -> Department:
    department = session.get(Department, department_id)
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found.")
    department.code = payload.code.strip()
    department.name = payload.name.strip()
    record_audit(session, actor, "update", "department", department.id)
    return department


@router.patch("/departments/{department_id}/archive", response_model=DepartmentView)
def archive_department(
    department_id: int,
    actor: AuthenticatedUser = Depends(require_roles("admin")),
    session: Session = Depends(get_db),
) -> Department:
    department = session.get(Department, department_id)
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found.")
    department.archived = True
    record_audit(session, actor, "archive", "department", department.id)
    return department


@router.get("/courses", response_model=list[CourseView])
def courses(
    department_id: int | None = None,
    actor: AuthenticatedUser = Depends(require_roles("admin", "teacher")),
    session: Session = Depends(get_db),
) -> list[Course]:
    query = select(Course).where(Course.archived.is_(False))
    if department_id:
        query = query.where(Course.department_id == department_id)
    return list(session.scalars(query.order_by(Course.name)))


@router.post("/courses", response_model=CourseView, status_code=201)
def create_course(
    payload: CourseInput,
    actor: AuthenticatedUser = Depends(require_roles("admin")),
    session: Session = Depends(get_db),
) -> Course:
    if session.get(Department, payload.department_id) is None:
        raise HTTPException(status_code=422, detail="Department not found.")
    return _save(session, actor, Course(**payload.model_dump()), "course")


@router.patch("/courses/{course_id}/archive", response_model=CourseView)
def archive_course(
    course_id: int,
    actor: AuthenticatedUser = Depends(require_roles("admin")),
    session: Session = Depends(get_db),
) -> Course:
    course = session.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found.")
    course.archived = True
    record_audit(session, actor, "archive", "course", course.id)
    return course


@router.get("/subjects", response_model=list[SubjectView])
def subjects(
    course_id: int | None = None,
    actor: AuthenticatedUser = Depends(require_roles("admin", "teacher")),
    session: Session = Depends(get_db),
) -> list[Subject]:
    query = select(Subject).where(Subject.archived.is_(False))
    if course_id:
        query = query.where(Subject.course_id == course_id)
    return list(session.scalars(query.order_by(Subject.name)))


@router.post("/subjects", response_model=SubjectView, status_code=201)
def create_subject(
    payload: SubjectInput,
    actor: AuthenticatedUser = Depends(require_roles("admin")),
    session: Session = Depends(get_db),
) -> Subject:
    if session.get(Course, payload.course_id) is None:
        raise HTTPException(status_code=422, detail="Course not found.")
    return _save(session, actor, Subject(**payload.model_dump()), "subject")


@router.patch("/subjects/{subject_id}/archive", response_model=SubjectView)
def archive_subject(
    subject_id: int,
    actor: AuthenticatedUser = Depends(require_roles("admin")),
    session: Session = Depends(get_db),
) -> Subject:
    subject = session.get(Subject, subject_id)
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found.")
    subject.archived = True
    record_audit(session, actor, "archive", "subject", subject.id)
    return subject


@router.get("/examinations", response_model=list[ExaminationView])
def examinations(
    subject_id: int | None = None,
    actor: AuthenticatedUser = Depends(require_roles("admin", "teacher")),
    session: Session = Depends(get_db),
) -> list[Examination]:
    query = select(Examination)
    if subject_id:
        query = query.where(Examination.subject_id == subject_id)
    return list(session.scalars(query.order_by(Examination.academic_year.desc(), Examination.name)))


@router.post("/examinations", response_model=ExaminationView, status_code=201)
def create_examination(
    payload: ExaminationInput,
    actor: AuthenticatedUser = Depends(require_roles("admin", "teacher")),
    session: Session = Depends(get_db),
) -> Examination:
    if session.get(Subject, payload.subject_id) is None:
        raise HTTPException(status_code=422, detail="Subject not found.")
    values = payload.model_dump()
    if values["exam_date"]:
        _date(values["exam_date"], "Exam date")
    return _save(session, actor, Examination(**values), "examination")


@router.get("/marks", response_model=list[MarkView])
def marks(
    examination_id: int | None = None,
    student_id: int | None = None,
    actor: AuthenticatedUser = Depends(require_roles("admin", "teacher")),
    session: Session = Depends(get_db),
) -> list[Mark]:
    query = select(Mark)
    if examination_id:
        query = query.where(Mark.examination_id == examination_id)
    if student_id:
        query = query.where(Mark.student_id == student_id)
    return list(session.scalars(query.order_by(Mark.id)))


@router.post("/marks", response_model=MarkView, status_code=201)
def create_mark(
    payload: MarkInput,
    actor: AuthenticatedUser = Depends(require_roles("admin", "teacher")),
    session: Session = Depends(get_db),
) -> Mark:
    examination = session.get(Examination, payload.examination_id)
    if examination is None or session.get(Student, payload.student_id) is None:
        raise HTTPException(status_code=422, detail="Examination or student not found.")
    if payload.score is not None and payload.score > float(examination.maximum_marks):
        raise HTTPException(status_code=422, detail="Score cannot exceed maximum marks.")
    return _save(session, actor, Mark(**payload.model_dump()), "mark")


@router.get("/attendance/students", response_model=list[StudentAttendanceView])
def student_attendance(
    student_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    actor: AuthenticatedUser = Depends(require_roles("admin", "teacher")),
    session: Session = Depends(get_db),
) -> list[StudentAttendance]:
    query = select(StudentAttendance)
    if student_id:
        query = query.where(StudentAttendance.student_id == student_id)
    if date_from:
        query = query.where(StudentAttendance.attendance_date >= _date(date_from, "Start date"))
    if date_to:
        query = query.where(StudentAttendance.attendance_date <= _date(date_to, "End date"))
    return list(session.scalars(query.order_by(StudentAttendance.attendance_date.desc())))


@router.post("/attendance/students", response_model=StudentAttendanceView, status_code=201)
def record_student_attendance(
    payload: StudentAttendanceInput,
    actor: AuthenticatedUser = Depends(require_roles("admin", "teacher")),
    session: Session = Depends(get_db),
) -> StudentAttendance:
    if payload.status not in {"present", "absent", "excused"}:
        raise HTTPException(status_code=422, detail="Student attendance status is invalid.")
    if session.get(Student, payload.student_id) is None:
        raise HTTPException(status_code=422, detail="Student not found.")
    values = payload.model_dump()
    values["attendance_date"] = _date(values["attendance_date"], "Attendance date")
    return _save(session, actor, StudentAttendance(**values), "student_attendance")


@router.get("/attendance/employees", response_model=list[EmployeeAttendanceView])
def employee_attendance(
    employee_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    actor: AuthenticatedUser = Depends(get_current_actor),
    session: Session = Depends(get_db),
) -> list[EmployeeAttendance]:
    if actor.role not in {"admin", "employee"}:
        raise HTTPException(status_code=403, detail="Not authorized.")
    if actor.role == "employee":
        employee_id = actor.employee_id
    query = select(EmployeeAttendance)
    if employee_id:
        query = query.where(EmployeeAttendance.employee_id == employee_id)
    if date_from:
        query = query.where(EmployeeAttendance.attendance_date >= _date(date_from, "Start date"))
    if date_to:
        query = query.where(EmployeeAttendance.attendance_date <= _date(date_to, "End date"))
    return list(session.scalars(query.order_by(EmployeeAttendance.attendance_date.desc())))


@router.post("/attendance/employees", response_model=EmployeeAttendanceView, status_code=201)
def record_employee_attendance(
    payload: EmployeeAttendanceInput,
    actor: AuthenticatedUser = Depends(require_roles("admin")),
    session: Session = Depends(get_db),
) -> EmployeeAttendance:
    if payload.status not in {"present", "absent", "leave"}:
        raise HTTPException(status_code=422, detail="Employee attendance status is invalid.")
    if session.get(Employee, payload.employee_id) is None:
        raise HTTPException(status_code=422, detail="Employee not found.")
    values = payload.model_dump()
    values["attendance_date"] = _date(values["attendance_date"], "Attendance date")
    return _save(session, actor, EmployeeAttendance(**values), "employee_attendance")


@router.get("/leaves", response_model=list[LeaveView])
def leaves(
    status_filter: str | None = Query(default=None, alias="status"),
    actor: AuthenticatedUser = Depends(get_current_actor),
    session: Session = Depends(get_db),
) -> list[LeaveRequest]:
    if actor.role not in {"admin", "teacher", "employee"}:
        raise HTTPException(status_code=403, detail="Not authorized.")
    query = select(LeaveRequest)
    if actor.role == "employee":
        query = query.where(LeaveRequest.employee_id == actor.employee_id)
    if status_filter:
        query = query.where(LeaveRequest.status == status_filter)
    return list(session.scalars(query.order_by(LeaveRequest.start_date.desc())))


@router.post("/leaves", response_model=LeaveView, status_code=201)
def request_leave(
    payload: LeaveInput,
    actor: AuthenticatedUser = Depends(get_current_actor),
    session: Session = Depends(get_db),
) -> LeaveRequest:
    values = payload.model_dump()
    values["start_date"] = _date(values["start_date"], "Start date")
    values["end_date"] = _date(values["end_date"], "End date")
    if actor.role == "employee":
        values["employee_id"] = actor.employee_id
        values["student_id"] = None
        values["status"] = "pending"
    elif actor.role == "teacher":
        if values["student_id"] is None:
            raise HTTPException(status_code=403, detail="Teachers may submit student leave only.")
        values["status"] = "pending"
    if values["student_id"] is not None and session.get(Student, values["student_id"]) is None:
        raise HTTPException(status_code=422, detail="Student not found.")
    if values["employee_id"] is not None and session.get(Employee, values["employee_id"]) is None:
        raise HTTPException(status_code=422, detail="Employee not found.")
    values["reviewed_by"] = None
    return _save(session, actor, LeaveRequest(**values), "leave_request")


@router.patch("/leaves/{leave_id}/decision", response_model=LeaveView)
def decide_leave(
    leave_id: int,
    decision: str,
    actor: AuthenticatedUser = Depends(require_roles("admin")),
    session: Session = Depends(get_db),
) -> LeaveRequest:
    if decision not in {"approved", "rejected"}:
        raise HTTPException(status_code=422, detail="Decision must be approved or rejected.")
    record = session.get(LeaveRequest, leave_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Leave request not found.")
    record.status = decision
    record.reviewed_by = actor.id
    record_audit(session, actor, decision, "leave_request", record.id)
    return record


@router.get("/activities", response_model=list[ActivityView])
def activities(
    student_id: int | None = None,
    actor: AuthenticatedUser = Depends(require_roles("admin", "teacher")),
    session: Session = Depends(get_db),
) -> list[Activity]:
    query = select(Activity)
    if student_id:
        query = query.where(Activity.student_id == student_id)
    return list(session.scalars(query.order_by(Activity.participation_date.desc())))


@router.post("/activities", response_model=ActivityView, status_code=201)
def create_activity(
    payload: ActivityInput,
    actor: AuthenticatedUser = Depends(require_roles("admin", "teacher")),
    session: Session = Depends(get_db),
) -> Activity:
    if session.get(Student, payload.student_id) is None:
        raise HTTPException(status_code=422, detail="Student not found.")
    values = payload.model_dump()
    values["participation_date"] = _date(values["participation_date"], "Participation date")
    return _save(session, actor, Activity(**values), "activity")


@router.get("/tasks", response_model=list[TaskView])
def tasks(
    employee_id: int | None = None,
    actor: AuthenticatedUser = Depends(get_current_actor),
    session: Session = Depends(get_db),
) -> list[EmployeeTask]:
    if actor.role == "employee":
        employee_id = actor.employee_id
    elif actor.role not in {"admin", "teacher"}:
        raise HTTPException(status_code=403, detail="Not authorized.")
    query = select(EmployeeTask)
    if employee_id:
        query = query.where(EmployeeTask.employee_id == employee_id)
    return list(session.scalars(query.order_by(EmployeeTask.deadline)))


@router.post("/tasks", response_model=TaskView, status_code=201)
def create_task(
    payload: TaskInput,
    actor: AuthenticatedUser = Depends(require_roles("admin", "teacher")),
    session: Session = Depends(get_db),
) -> EmployeeTask:
    if payload.status not in {"todo", "in_progress", "completed", "blocked"}:
        raise HTTPException(status_code=422, detail="Task status is invalid.")
    if session.get(Employee, payload.employee_id) is None:
        raise HTTPException(status_code=422, detail="Employee not found.")
    values = payload.model_dump()
    values["assigned_date"] = _date(values["assigned_date"], "Assigned date")
    if values["deadline"]:
        values["deadline"] = _date(values["deadline"], "Deadline")
    return _save(session, actor, EmployeeTask(**values), "employee_task")


@router.patch("/tasks/{task_id}/status", response_model=TaskView)
def update_task_status(
    task_id: int,
    task_status: str,
    actor: AuthenticatedUser = Depends(get_current_actor),
    session: Session = Depends(get_db),
) -> EmployeeTask:
    if task_status not in {"todo", "in_progress", "completed", "blocked"}:
        raise HTTPException(status_code=422, detail="Task status is invalid.")
    record = session.get(EmployeeTask, task_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    if actor.role == "employee" and record.employee_id != actor.employee_id:
        raise HTTPException(status_code=403, detail="Employees may update only their assigned tasks.")
    if actor.role not in {"admin", "teacher", "employee"}:
        raise HTTPException(status_code=403, detail="Not authorized.")
    record.status = task_status
    record_audit(session, actor, "update_status", "employee_task", record.id)
    return record


@router.get("/reviews", response_model=list[ReviewView])
def reviews(
    employee_id: int | None = None,
    actor: AuthenticatedUser = Depends(get_current_actor),
    session: Session = Depends(get_db),
) -> list[PerformanceReview]:
    if actor.role == "employee":
        employee_id = actor.employee_id
    elif actor.role not in {"admin", "teacher"}:
        raise HTTPException(status_code=403, detail="Not authorized.")
    query = select(PerformanceReview)
    if employee_id:
        query = query.where(PerformanceReview.employee_id == employee_id)
    return list(session.scalars(query.order_by(PerformanceReview.period_end.desc())))


@router.post("/reviews", response_model=ReviewView, status_code=201)
def create_review(
    payload: ReviewInput,
    actor: AuthenticatedUser = Depends(require_roles("admin", "teacher")),
    session: Session = Depends(get_db),
) -> PerformanceReview:
    if session.get(Employee, payload.employee_id) is None:
        raise HTTPException(status_code=422, detail="Employee not found.")
    values = payload.model_dump()
    values["period_start"] = _date(values["period_start"], "Period start")
    values["period_end"] = _date(values["period_end"], "Period end")
    if values["period_start"] > values["period_end"]:
        raise HTTPException(status_code=422, detail="Review period start must not follow period end.")
    values["reviewer_id"] = actor.id
    return _save(session, actor, PerformanceReview(**values), "performance_review")