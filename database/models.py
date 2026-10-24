from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'teacher', 'employee')", name="ck_users_role"),
        CheckConstraint(
            "role != 'employee' OR employee_id IS NOT NULL",
            name="ck_employee_user_has_profile",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80, collation="NOCASE"), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"), unique=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False
    )

    employee: Mapped["Employee | None"] = relationship(back_populates="user")


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (
        CheckConstraint(
            "enrollment_status IS NULL OR enrollment_status IN "
            "('active', 'withdrawn', 'graduated', 'suspended', 'archived')",
            name="ck_students_enrollment_status",
        ),
        Index(
            "uq_students_admission_number",
            "admission_number",
            unique=True,
            sqlite_where=text("admission_number IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    register_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    admission_number: Mapped[str | None] = mapped_column(String(50))
    date_of_birth: Mapped[str | None] = mapped_column(String(10))
    email: Mapped[str | None] = mapped_column(String(254))
    phone: Mapped[str | None] = mapped_column(String(40))
    address: Mapped[str | None] = mapped_column(String(500))
    guardian_name: Mapped[str | None] = mapped_column(String(160))
    guardian_contact: Mapped[str | None] = mapped_column(String(80))
    course: Mapped[str | None] = mapped_column(String(120))
    department: Mapped[str | None] = mapped_column(String(120))
    branch: Mapped[str | None] = mapped_column(String(120))
    academic_year: Mapped[str | None] = mapped_column(String(30))
    current_semester: Mapped[str | None] = mapped_column(String(30))
    section: Mapped[str | None] = mapped_column(String(30))
    admission_date: Mapped[str | None] = mapped_column(String(10))
    enrollment_status: Mapped[str | None] = mapped_column(String(20), default="active")
    profile_image_path: Mapped[str | None] = mapped_column(String(500))


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    department: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    designation: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    work_email: Mapped[str | None] = mapped_column(String(254))
    work_phone: Mapped[str | None] = mapped_column(String(40))
    joining_date: Mapped[str | None] = mapped_column(String(10))
    employment_status: Mapped[str | None] = mapped_column(String(20), default="active")
    reporting_manager: Mapped[str | None] = mapped_column(String(160))
    emergency_contact: Mapped[str | None] = mapped_column(String(80))
    skills: Mapped[str | None] = mapped_column(String(2000))
    certifications: Mapped[str | None] = mapped_column(String(2000))
    profile_image_path: Mapped[str | None] = mapped_column(String(500))

    user: Mapped[User | None] = relationship(back_populates="employee", uselist=False)