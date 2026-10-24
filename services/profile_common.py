from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


class DuplicateProfileError(ValueError):
    """Raised when a unique profile identifier is already in use."""


class ProfileValidationError(ValueError):
    """Raised when profile input does not meet field rules."""


def normalize_profile(values: dict[str, Any], required: tuple[str, ...]) -> dict[str, Any]:
    normalized = {key: value.strip() if isinstance(value, str) else value for key, value in values.items()}
    for field in required:
        if not normalized[field]:
            raise ProfileValidationError(f"{field.replace('_', ' ').title()} is required.")

    date_fields = ("date_of_birth", "admission_date", "joining_date")
    for field in date_fields:
        value = normalized.get(field)
        if value:
            try:
                date.fromisoformat(value)
            except (TypeError, ValueError) as error:
                raise ProfileValidationError(f"{field.replace('_', ' ').title()} must use YYYY-MM-DD.") from error

    email_fields = ("email", "work_email")
    for field in email_fields:
        value = normalized.get(field)
        if value and ("@" not in value or "." not in value.rsplit("@", 1)[-1]):
            raise ProfileValidationError(f"{field.replace('_', ' ').title()} is invalid.")

    for field, maximum in {
        "register_number": 50,
        "admission_number": 50,
        "employee_code": 50,
        "full_name": 160,
        "email": 254,
        "work_email": 254,
        "phone": 40,
        "work_phone": 40,
    }.items():
        value = normalized.get(field)
        if value and len(value) > maximum:
            raise ProfileValidationError(f"{field.replace('_', ' ').title()} exceeds {maximum} characters.")
    return normalized


def save_profile(session: Session, instance: Any, duplicate_query: Any, duplicate_message: str) -> Any:
    if session.scalar(select(duplicate_query)):
        raise DuplicateProfileError(duplicate_message)
    session.add(instance)
    try:
        session.flush()
    except IntegrityError as error:
        session.rollback()
        raise DuplicateProfileError(duplicate_message) from error
    return instance