import json
import os

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.dependencies import get_db, require_roles
from database.academic_models import (
    EmployeeAttendance,
    EmployeeTask,
    Examination,
    Mark,
    PerformanceReview,
    StudentAttendance,
    Subject,
)
from database.models import Employee, Student
from services.auth_service import AuthenticatedUser


router = APIRouter(prefix="/analytics", tags=["analytics"])
DEFAULT_GRADE_THRESHOLDS = {"A": 90, "B": 80, "C": 70, "D": 60}


def _grade_thresholds() -> dict[str, float]:
    configured = os.environ.get("SPS_GRADE_THRESHOLDS")
    if not configured:
        return DEFAULT_GRADE_THRESHOLDS
    try:
        values = json.loads(configured)
        thresholds = {str(name): float(value) for name, value in values.items()}
        if not thresholds or any(value < 0 or value > 100 for value in thresholds.values()):
            raise ValueError
        return dict(sorted(thresholds.items(), key=lambda pair: pair[1], reverse=True))
    except (AttributeError, TypeError, ValueError, json.JSONDecodeError):
        return DEFAULT_GRADE_THRESHOLDS


@router.get("/overview")
def overview(
    actor: AuthenticatedUser = Depends(require_roles("admin", "teacher", "employee")),
    session: Session = Depends(get_db),
) -> dict[str, object]:
    if actor.role == "employee":
        active_task_count = session.scalar(
            select(func.count()).select_from(EmployeeTask).where(
                EmployeeTask.employee_id == actor.employee_id,
                EmployeeTask.status != "completed",
            )
        ) or 0
        return {
            "total_students": None,
            "total_employees": None,
            "pending_tasks": active_task_count,
            "average_marks_percentage": None,
            "pass_percentage": None,
            "attendance_percentage": None,
        }

    total_students = session.scalar(
        select(func.count()).select_from(Student).where(Student.archived.is_(False))
    ) or 0
    total_employees = session.scalar(
        select(func.count()).select_from(Employee).where(Employee.active.is_(True))
    ) or 0
    pending_tasks = session.scalar(
        select(func.count()).select_from(EmployeeTask).where(EmployeeTask.status != "completed")
    ) or 0

    mark_rows = session.execute(
        select(Mark.score, Examination.maximum_marks, Examination.pass_marks)
        .join(Examination, Examination.id == Mark.examination_id)
        .where(Mark.status == "entered", Mark.score.is_not(None))
    ).all()
    average_marks = pass_percentage = None
    if mark_rows:
        percentages = np.array([float(score) / float(maximum) * 100 for score, maximum, _ in mark_rows])
        passed = np.array([float(score) >= float(pass_mark) for score, _, pass_mark in mark_rows])
        average_marks = round(float(np.mean(percentages)), 2)
        pass_percentage = round(float(np.mean(passed) * 100), 2)

    attendance_rows = session.execute(
        select(StudentAttendance.status).where(StudentAttendance.status.in_(("present", "absent")))
    ).all()
    attendance_percentage = None
    if attendance_rows:
        attendance_percentage = round(
            float(np.mean([status == "present" for (status,) in attendance_rows]) * 100), 2
        )

    return {
        "total_students": total_students,
        "total_employees": total_employees,
        "pending_tasks": pending_tasks,
        "average_marks_percentage": average_marks,
        "pass_percentage": pass_percentage,
        "attendance_percentage": attendance_percentage,
    }


@router.get("/academic")
def academic_analytics(
    actor: AuthenticatedUser = Depends(require_roles("admin", "teacher")),
    session: Session = Depends(get_db),
) -> dict[str, object]:
    rows = session.execute(
        select(
            Mark.student_id,
            Student.full_name,
            Student.academic_year,
            Student.current_semester,
            Mark.score,
            Examination.maximum_marks,
            Examination.pass_marks,
            Examination.academic_year.label("exam_year"),
            Examination.semester.label("exam_semester"),
            Subject.code.label("subject_code"),
            Subject.name.label("subject_name"),
        )
        .join(Student, Student.id == Mark.student_id)
        .join(Examination, Examination.id == Mark.examination_id)
        .join(Subject, Subject.id == Examination.subject_id)
        .where(Mark.status == "entered", Mark.score.is_not(None))
    ).all()
    columns = ["student_id", "student_name", "student_year", "student_semester", "score", "maximum", "pass_mark", "year", "semester", "subject_code", "subject_name"]
    dataframe = pd.DataFrame(rows, columns=columns)
    if dataframe.empty:
        return {
            "subject_averages": [],
            "performance_trends": [],
            "grade_distribution": [],
            "class_summaries": [],
            "grade_thresholds": _grade_thresholds(),
            "entered_mark_count": 0,
            "excluded_pending_or_absent": session.scalar(
                select(func.count()).select_from(Mark).where(Mark.status.in_(("pending", "absent")))
            ) or 0,
        }

    dataframe["percentage"] = dataframe["score"].astype(float) / dataframe["maximum"].astype(float) * 100
    dataframe["passed"] = dataframe["score"].astype(float) >= dataframe["pass_mark"].astype(float)
    subjects = (
        dataframe.groupby(["subject_code", "subject_name"], as_index=False)
        .agg(average_percentage=("percentage", "mean"), entered_marks=("percentage", "count"))
    )
    trends = (
        dataframe.groupby(["year", "semester"], as_index=False)
        .agg(average_percentage=("percentage", "mean"), pass_percentage=("passed", "mean"), mark_count=("score", "count"))
        .sort_values(["year", "semester"])
    )
    grades = []
    remaining = np.ones(len(dataframe), dtype=bool)
    for label, threshold in _grade_thresholds().items():
        matching = remaining & (dataframe["percentage"].to_numpy() >= threshold)
        grades.append({"grade": label, "count": int(matching.sum())})
        remaining &= ~matching
    grades.append({"grade": "Below threshold", "count": int(remaining.sum())})
    classes = (
        dataframe.groupby(["year", "semester"], as_index=False)
        .agg(average_percentage=("percentage", "mean"), pass_percentage=("passed", "mean"), student_results=("student_id", "count"))
    )
    excluded = session.scalar(
        select(func.count()).select_from(Mark).where(Mark.status.in_(("pending", "absent")))
    ) or 0
    return {
        "subject_averages": subjects.round(2).to_dict(orient="records"),
        "performance_trends": trends.assign(pass_percentage=trends["pass_percentage"] * 100).round(2).to_dict(orient="records"),
        "grade_distribution": grades,
        "class_summaries": classes.assign(pass_percentage=classes["pass_percentage"] * 100).round(2).to_dict(orient="records"),
        "grade_thresholds": _grade_thresholds(),
        "entered_mark_count": int(len(dataframe)),
        "excluded_pending_or_absent": excluded,
    }


@router.get("/attendance")
def attendance_analytics(
    actor: AuthenticatedUser = Depends(require_roles("admin", "teacher")),
    session: Session = Depends(get_db),
) -> dict[str, object]:
    student_rows = session.execute(
        select(StudentAttendance.attendance_date, StudentAttendance.status)
    ).all()
    employee_rows = session.execute(
        select(EmployeeAttendance.attendance_date, EmployeeAttendance.status)
    ).all()
    student_frame = pd.DataFrame(student_rows, columns=["date", "status"])
    employee_frame = pd.DataFrame(employee_rows, columns=["date", "status"])

    def summarize(frame: pd.DataFrame, eligible: set[str]) -> list[dict[str, object]]:
        if frame.empty:
            return []
        frame = frame[frame["status"].isin(eligible)].copy()
        if frame.empty:
            return []
        frame["present"] = frame["status"].eq("present")
        summary = frame.groupby("date", as_index=False).agg(
            present=("present", "sum"), eligible=("present", "count")
        )
        summary["attendance_percentage"] = summary["present"] / summary["eligible"] * 100
        return summary.round(2).to_dict(orient="records")

    return {
        "student_trend": summarize(student_frame, {"present", "absent"}),
        "employee_trend": summarize(employee_frame, {"present", "absent"}),
        "denominator": "scheduled attendance rows with present or absent status; excused/leave excluded",
    }


@router.get("/employees")
def employee_analytics(
    actor: AuthenticatedUser = Depends(require_roles("admin", "teacher")),
    session: Session = Depends(get_db),
) -> dict[str, object]:
    tasks = session.execute(
        select(EmployeeTask.employee_id, Employee.full_name, Employee.department, EmployeeTask.status)
        .join(Employee, Employee.id == EmployeeTask.employee_id)
    ).all()
    task_frame = pd.DataFrame(tasks, columns=["employee_id", "employee_name", "department", "status"])
    if task_frame.empty:
        task_summary: list[dict[str, object]] = []
    else:
        task_frame["completed"] = task_frame["status"].eq("completed")
        grouped = task_frame.groupby(["employee_id", "employee_name", "department"], as_index=False).agg(
            completed_tasks=("completed", "sum"), total_tasks=("status", "count")
        )
        grouped["completion_percentage"] = grouped["completed_tasks"] / grouped["total_tasks"] * 100
        task_summary = grouped.round(2).to_dict(orient="records")

    review_rows = session.execute(
        select(PerformanceReview.employee_id, Employee.full_name, PerformanceReview.score)
        .join(Employee, Employee.id == PerformanceReview.employee_id)
        .where(PerformanceReview.score.is_not(None))
    ).all()
    review_frame = pd.DataFrame(review_rows, columns=["employee_id", "employee_name", "score"])
    if review_frame.empty:
        review_summary: list[dict[str, object]] = []
    else:
        review_summary = review_frame.groupby(["employee_id", "employee_name"], as_index=False).agg(
            average_review_score=("score", "mean"), review_count=("score", "count")
        ).round(2).to_dict(orient="records")
    return {
        "task_completion": task_summary,
        "review_summaries": review_summary,
        "note": "Task completion and documented review scores are separate summaries; neither is an automatic employment rating.",
    }