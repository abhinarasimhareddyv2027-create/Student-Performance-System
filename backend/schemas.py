from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginInput(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=256)


class UserView(ORMModel):
    id: int
    username: str
    role: str
    employee_id: int | None = None


class StudentView(ORMModel):
    id: int
    register_number: str
    full_name: str
    archived: bool
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
    enrollment_status: str | None = None


class EmployeeView(ORMModel):
    id: int
    employee_code: str
    full_name: str
    department: str
    designation: str
    active: bool
    work_email: str | None = None
    work_phone: str | None = None
    joining_date: str | None = None
    employment_status: str | None = None
    reporting_manager: str | None = None
    emergency_contact: str | None = None
    skills: str | None = None
    certifications: str | None = None


class DepartmentView(ORMModel):
    id: int
    code: str
    name: str
    archived: bool


class CourseView(ORMModel):
    id: int
    department_id: int
    code: str
    name: str
    archived: bool


class SubjectView(ORMModel):
    id: int
    course_id: int
    code: str
    name: str
    archived: bool


class ExaminationView(ORMModel):
    id: int
    subject_id: int
    name: str
    academic_year: str
    semester: str
    exam_date: str | None
    maximum_marks: float
    pass_marks: float


class MarkView(ORMModel):
    id: int
    examination_id: int
    student_id: int
    status: str
    score: float | None


class StudentAttendanceView(ORMModel):
    id: int
    student_id: int
    attendance_date: str
    session: str
    status: str
    note: str | None


class EmployeeAttendanceView(ORMModel):
    id: int
    employee_id: int
    attendance_date: str
    shift: str
    status: str
    check_in: str | None
    check_out: str | None


class LeaveView(ORMModel):
    id: int
    student_id: int | None
    employee_id: int | None
    start_date: str
    end_date: str
    reason: str
    status: str


class ActivityView(ORMModel):
    id: int
    student_id: int
    title: str
    category: str
    participation_date: str
    description: str | None


class TaskView(ORMModel):
    id: int
    employee_id: int
    title: str
    description: str | None
    project: str | None
    assigned_date: str
    deadline: str | None
    status: str
    completion_notes: str | None


class ReviewView(ORMModel):
    id: int
    employee_id: int
    reviewer_id: int | None
    period_start: str
    period_end: str
    criteria: str
    score: float | None
    feedback: str


class ProfileInput(BaseModel):
    full_name: str = Field(min_length=1, max_length=160)

    @field_validator("full_name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Full name is required.")
        return value


class StudentInput(ProfileInput):
    register_number: str = Field(min_length=1, max_length=50)
    admission_number: str | None = Field(default=None, max_length=50)
    date_of_birth: str | None = None
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=40)
    address: str | None = Field(default=None, max_length=500)
    guardian_name: str | None = Field(default=None, max_length=160)
    guardian_contact: str | None = Field(default=None, max_length=80)
    course: str | None = Field(default=None, max_length=120)
    department: str | None = Field(default=None, max_length=120)
    branch: str | None = Field(default=None, max_length=120)
    academic_year: str | None = Field(default=None, max_length=30)
    current_semester: str | None = Field(default=None, max_length=30)
    section: str | None = Field(default=None, max_length=30)
    admission_date: str | None = None
    enrollment_status: str = "active"

    @field_validator("register_number")
    @classmethod
    def trim_register(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Register number is required.")
        return value


class EmployeeInput(ProfileInput):
    employee_code: str = Field(min_length=1, max_length=50)
    department: str = Field(default="", max_length=120)
    designation: str = Field(default="", max_length=120)
    work_email: str | None = Field(default=None, max_length=254)
    work_phone: str | None = Field(default=None, max_length=40)
    joining_date: str | None = None
    employment_status: str = "active"
    reporting_manager: str | None = Field(default=None, max_length=160)
    emergency_contact: str | None = Field(default=None, max_length=80)
    skills: str | None = Field(default=None, max_length=2000)
    certifications: str | None = Field(default=None, max_length=2000)

    @field_validator("employee_code")
    @classmethod
    def trim_code(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Employee code is required.")
        return value


class DepartmentInput(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=120)


class CourseInput(BaseModel):
    department_id: int = Field(gt=0)
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=160)


class SubjectInput(BaseModel):
    course_id: int = Field(gt=0)
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=160)


class ExaminationInput(BaseModel):
    subject_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=120)
    academic_year: str = Field(min_length=1, max_length=30)
    semester: str = Field(min_length=1, max_length=30)
    exam_date: str | None = None
    maximum_marks: float = Field(gt=0, le=100000)
    pass_marks: float = Field(ge=0, le=100000)

    @model_validator(mode="after")
    def pass_mark_within_maximum(self) -> "ExaminationInput":
        if self.pass_marks > self.maximum_marks:
            raise ValueError("Pass marks cannot exceed maximum marks.")
        return self


class MarkInput(BaseModel):
    examination_id: int = Field(gt=0)
    student_id: int = Field(gt=0)
    status: str = "pending"
    score: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def status_matches_score(self) -> "MarkInput":
        if self.status not in {"pending", "absent", "entered"}:
            raise ValueError("Mark status must be pending, absent, or entered.")
        if (self.status == "entered") != (self.score is not None):
            raise ValueError("Only entered marks require a numeric score; pending and absent marks have no score.")
        return self


class StudentAttendanceInput(BaseModel):
    student_id: int = Field(gt=0)
    attendance_date: str
    session: str = Field(default="day", min_length=1, max_length=40)
    status: str
    note: str | None = Field(default=None, max_length=500)


class EmployeeAttendanceInput(BaseModel):
    employee_id: int = Field(gt=0)
    attendance_date: str
    shift: str = Field(default="day", min_length=1, max_length=40)
    status: str
    check_in: str | None = None
    check_out: str | None = None


class LeaveInput(BaseModel):
    student_id: int | None = Field(default=None, gt=0)
    employee_id: int | None = Field(default=None, gt=0)
    start_date: str
    end_date: str
    reason: str = Field(min_length=1, max_length=1000)
    status: str = "pending"

    @model_validator(mode="after")
    def owner_and_status(self) -> "LeaveInput":
        if (self.student_id is None) == (self.employee_id is None):
            raise ValueError("Specify exactly one student or employee owner.")
        if self.status not in {"pending", "approved", "rejected"}:
            raise ValueError("Leave status is invalid.")
        if self.start_date > self.end_date:
            raise ValueError("Leave start date must not be after end date.")
        return self


class ActivityInput(BaseModel):
    student_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=180)
    category: str = Field(min_length=1, max_length=60)
    participation_date: str
    description: str | None = None


class TaskInput(BaseModel):
    employee_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=180)
    description: str | None = None
    project: str | None = Field(default=None, max_length=160)
    assigned_date: str
    deadline: str | None = None
    status: str = "todo"
    completion_notes: str | None = None


class ReviewInput(BaseModel):
    employee_id: int = Field(gt=0)
    period_start: str
    period_end: str
    criteria: str = Field(min_length=1, max_length=500)
    score: float | None = Field(default=None, ge=0, le=100)
    feedback: str = Field(min_length=1)


class UserCreateInput(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=12, max_length=256)
    role: str
    employee_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_role(self) -> "UserCreateInput":
        if self.role not in {"admin", "teacher", "employee"}:
            raise ValueError("Role is invalid.")
        if self.role == "employee" and self.employee_id is None:
            raise ValueError("Employee accounts must be linked to an employee profile.")
        return self