from collections.abc import Callable
from getpass import getpass

from sqlalchemy.orm import sessionmaker

from database.connection import SessionLocal, session_scope
from services.auth_service import authenticate_user
from services.dashboard_service import get_dashboard_summary


def run_console(
    session_factory: sessionmaker = SessionLocal,
    username_reader: Callable[[str], str] | None = None,
    password_reader: Callable[[str], str] | None = None,
    output: Callable[[str], None] | None = None,
) -> int:
    username_reader = username_reader or input
    password_reader = password_reader or getpass
    output = output or print

    output("No graphical display detected. Starting the terminal dashboard.")
    with session_scope(session_factory) as session:
        actor = authenticate_user(
            session,
            username_reader("Username: "),
            password_reader("Password: "),
        )
        if actor is None:
            output("Sign-in failed. Check your details or contact an administrator.")
            return 1
        summary = get_dashboard_summary(session, actor)

    output(f"Signed in as {actor.username} ({actor.role}).")
    output("Dashboard")
    output(f"Students: {summary.total_students if summary.total_students is not None else 'Restricted'}")
    output(f"Employees: {summary.total_employees if summary.total_employees is not None else 'Restricted'}")
    output("This terminal view is read-only. Run the app in a desktop session to manage profiles.")
    return 0