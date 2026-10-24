import argparse
from getpass import getpass
import os
import sys

import customtkinter as ctk

from database.connection import SessionLocal, initialize_database, session_scope
from services.auth_service import AuthenticationError, AuthenticatedUser, create_initial_admin
from ui.dashboard import DashboardScreen
from ui.console import run_console
from ui.employees import EmployeeScreen
from ui.login import LoginScreen
from ui.students import StudentScreen


class Application(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Student & Employee Performance System")
        self.geometry("1120x700")
        self.minsize(780, 560)
        self.configure(fg_color="#101827")
        self._show_login()

    def _show_login(self) -> None:
        self._clear_screen()
        screen = LoginScreen(self, SessionLocal, self._show_dashboard)
        screen.pack(fill="both", expand=True)

    def _show_dashboard(self, actor: AuthenticatedUser) -> None:
        self._clear_screen()
        screen = DashboardScreen(
            self,
            SessionLocal,
            actor,
            self._show_login,
            lambda: self._open_student_window(actor),
            lambda: self._open_employee_window(actor),
        )
        screen.pack(fill="both", expand=True)

    def _open_student_window(self, actor: AuthenticatedUser) -> None:
        window = ctk.CTkToplevel(self)
        window.title("Student profiles")
        window.geometry("1180x720")
        StudentScreen(window, SessionLocal, actor).pack(fill="both", expand=True)

    def _open_employee_window(self, actor: AuthenticatedUser) -> None:
        window = ctk.CTkToplevel(self)
        window.title("Employee profiles" if actor.role == "admin" else "My profile")
        window.geometry("1180x720")
        EmployeeScreen(window, SessionLocal, actor).pack(fill="both", expand=True)

    def _clear_screen(self) -> None:
        for child in self.winfo_children():
            child.destroy()


def setup_initial_admin() -> int:
    username = input("Admin username: ").strip()
    password = getpass("Admin password (minimum 12 characters): ")
    confirmation = getpass("Confirm password: ")
    if password != confirmation:
        print("Passwords do not match.")
        return 1

    try:
        with session_scope() as session:
            user = create_initial_admin(session, username, password)
        print(f"Initial admin account created for {user.username!r}.")
        return 0
    except AuthenticationError as error:
        print(error)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Student and Employee Performance Management System")
    parser.add_argument(
        "--setup-admin",
        action="store_true",
        help="Create the first admin account in an empty user store.",
    )
    args = parser.parse_args()
    initialize_database()

    if args.setup_admin:
        return setup_initial_admin()

    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        return run_console()

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    Application().mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())