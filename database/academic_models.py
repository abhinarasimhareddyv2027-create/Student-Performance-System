from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    archived: Mapped[bool] = mapped_column(default=False, nullable=False)


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id", ondelete="RESTRICT"), index=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    archived: Mapped[bool] = mapped_column(default=False, nullable=False)

    department: Mapped[Department] = relationship()


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"), index=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    archived: Mapped[bool] = mapped_column(default=False, nullable=False)

    course: Mapped[Course] = relationship()


class Examination(Base):
    __tablename__ = "examinations"
    __table_args__ = (
        UniqueConstraint("subject_id", "name", "academic_year", "semester", name="uq_exam_period"),
        CheckConstraint("maximum_marks > 0", name="ck_exam_maximum_positive"),
        CheckConstraint("pass_marks >= 0 AND pass_marks <= maximum_marks", name="ck_exam_pass_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    academic_year: Mapped[str] = mapped_column(String(30))
    semester: Mapped[str] = mapped_column(String(30))
    exam_date: Mapped[str | None] = mapped_column(String(10))
    maximum_marks: Mapped[float] = mapped_column(Numeric(8, 2))
    pass_marks: Mapped[float] = mapped_column(Numeric(8, 2))

    subject: Mapped[Subject] = relationship()


class Mark(Base):
    __tablename__ = "marks"
    __table_args__ = (
        UniqueConstraint("examination_id", "student_id", name="uq_mark_exam_student"),
        CheckConstraint("status IN ('pending', 'absent', 'entered')", name="ck_mark_status"),
        CheckConstraint(
            "(status = 'entered' AND score IS NOT NULL AND score >= 0) OR "
            "(status IN ('pending', 'absent') AND score IS NULL)",
            name="ck_mark_value_matches_status",
        ),
        Index("ix_marks_student_exam", "student_id", "examination_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    examination_id: Mapped[int] = mapped_column(ForeignKey("examinations.id", ondelete="RESTRICT"))
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="RESTRICT"))
    status: Mapped[str] = mapped_column(String(12), default="pending")
    score: Mapped[float | None] = mapped_column(Numeric(8, 2))


class StudentAttendance(Base):
    __tablename__ = "student_attendance"
    __table_args__ = (
        UniqueConstraint("student_id", "attendance_date", "session", name="uq_student_attendance_session"),
        CheckConstraint("status IN ('present', 'absent', 'excused')", name="ck_student_attendance_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="RESTRICT"), index=True)
    attendance_date: Mapped[str] = mapped_column(String(10), index=True)
    session: Mapped[str] = mapped_column(String(40), default="day")
    status: Mapped[str] = mapped_column(String(12))
    note: Mapped[str | None] = mapped_column(String(500))


class EmployeeAttendance(Base):
    __tablename__ = "employee_attendance"
    __table_args__ = (
        UniqueConstraint("employee_id", "attendance_date", "shift", name="uq_employee_attendance_shift"),
        CheckConstraint("status IN ('present', 'absent', 'leave')", name="ck_employee_attendance_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="RESTRICT"), index=True)
    attendance_date: Mapped[str] = mapped_column(String(10), index=True)
    shift: Mapped[str] = mapped_column(String(40), default="day")
    status: Mapped[str] = mapped_column(String(12))
    check_in: Mapped[str | None] = mapped_column(String(8))
    check_out: Mapped[str | None] = mapped_column(String(8))


class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    __table_args__ = (
        CheckConstraint(
            "(student_id IS NOT NULL AND employee_id IS NULL) OR "
            "(student_id IS NULL AND employee_id IS NOT NULL)",
            name="ck_leave_exactly_one_owner",
        ),
        CheckConstraint("start_date <= end_date", name="ck_leave_date_range"),
        CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="ck_leave_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int | None] = mapped_column(ForeignKey("students.id", ondelete="RESTRICT"), index=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id", ondelete="RESTRICT"), index=True)
    start_date: Mapped[str] = mapped_column(String(10))
    end_date: Mapped[str] = mapped_column(String(10))
    reason: Mapped[str] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(12), default="pending")
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp())


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="RESTRICT"), index=True)
    title: Mapped[str] = mapped_column(String(180))
    category: Mapped[str] = mapped_column(String(60))
    participation_date: Mapped[str] = mapped_column(String(10), index=True)
    description: Mapped[str | None] = mapped_column(Text)


class EmployeeTask(Base):
    __tablename__ = "employee_tasks"
    __table_args__ = (
        CheckConstraint("status IN ('todo', 'in_progress', 'completed', 'blocked')", name="ck_task_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="RESTRICT"), index=True)
    title: Mapped[str] = mapped_column(String(180))
    description: Mapped[str | None] = mapped_column(Text)
    project: Mapped[str | None] = mapped_column(String(160))
    assigned_date: Mapped[str] = mapped_column(String(10))
    deadline: Mapped[str | None] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20), default="todo")
    completion_notes: Mapped[str | None] = mapped_column(Text)


class PerformanceReview(Base):
    __tablename__ = "performance_reviews"
    __table_args__ = (
        CheckConstraint("period_start <= period_end", name="ck_review_period"),
        CheckConstraint("score IS NULL OR (score >= 0 AND score <= 100)", name="ck_review_score_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="RESTRICT"), index=True)
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    period_start: Mapped[str] = mapped_column(String(10))
    period_end: Mapped[str] = mapped_column(String(10))
    criteria: Mapped[str] = mapped_column(String(500))
    score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    feedback: Mapped[str] = mapped_column(Text)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    action: Mapped[str] = mapped_column(String(80))
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[int | None] = mapped_column(Integer)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.current_timestamp())
    detail: Mapped[str | None] = mapped_column(Text)