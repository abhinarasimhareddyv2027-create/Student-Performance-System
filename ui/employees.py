from collections.abc import Callable
from dataclasses import fields
from tkinter import messagebox, ttk

import customtkinter as ctk
from sqlalchemy.orm import sessionmaker

from database.connection import session_scope
from database.models import Employee
from services.auth_service import AuthenticatedUser
from services.employee_service import (
    EMPLOYMENT_STATUSES,
    EmployeeProfile,
    archive_employee,
    create_employee,
    get_employee,
    list_employees,
    update_employee,
)


EMPLOYEE_FIELDS = (
    "employee_code",
    "full_name",
    "department",
    "designation",
    "work_email",
    "work_phone",
    "joining_date",
    "employment_status",
    "reporting_manager",
    "emergency_contact",
    "skills",
    "certifications",
)
EMPLOYEE_LABELS = {
    "employee_code": "Employee code *",
    "full_name": "Full name *",
    "work_email": "Work email",
    "work_phone": "Work phone",
    "joining_date": "Joining date (YYYY-MM-DD)",
    "employment_status": "Employment status",
    "reporting_manager": "Reporting manager",
    "emergency_contact": "Emergency contact",
}


class EmployeeScreen(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkToplevel, session_factory: sessionmaker, actor: AuthenticatedUser) -> None:
        super().__init__(master, fg_color="#101827")
        self.session_factory = session_factory
        self.actor = actor
        if actor.role == "employee":
            self._show_own_profile()
            return
        if actor.role != "admin":
            raise PermissionError("Employee profile management is restricted to administrators.")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        heading = ctk.CTkFrame(self, fg_color="transparent")
        heading.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 8))
        ctk.CTkLabel(heading, text="Employees", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        ctk.CTkButton(heading, text="Add employee", command=self._add, width=130).pack(side="right")

        filters = ctk.CTkFrame(self, fg_color="transparent")
        filters.grid(row=1, column=0, sticky="ew", padx=24, pady=8)
        self.search_entry = ctk.CTkEntry(filters, placeholder_text="Search name or employee code", width=280)
        self.search_entry.pack(side="left", padx=(0, 8))
        self.department_entry = ctk.CTkEntry(filters, placeholder_text="Department", width=160)
        self.department_entry.pack(side="left", padx=4)
        self.designation_entry = ctk.CTkEntry(filters, placeholder_text="Designation", width=160)
        self.designation_entry.pack(side="left", padx=4)
        self.search_entry.bind("<Return>", lambda _event: self._refresh())
        ctk.CTkButton(filters, text="Search", command=self._refresh, width=76).pack(side="left", padx=8)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="new", padx=24, pady=(0, 8))
        ctk.CTkButton(actions, text="Edit selected", command=self._edit, width=120).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            actions,
            text="Archive selected",
            command=self._archive,
            width=140,
            fg_color="#8F4147",
            hover_color="#71343A",
        ).pack(side="left")

        table_frame = ctk.CTkFrame(self, fg_color="transparent")
        table_frame.grid(row=3, column=0, sticky="nsew", padx=24, pady=(0, 24))
        self.grid_rowconfigure(3, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        columns = ("code", "name", "department", "designation", "email", "phone", "status")
        self.table = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        titles = ("Employee code", "Full name", "Department", "Designation", "Work email", "Phone", "Status")
        widths = (110, 190, 140, 140, 210, 120, 100)
        for key, title, width in zip(columns, titles, widths):
            self.table.heading(key, text=title)
            self.table.column(key, width=width, minwidth=70, stretch=True)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.table.bind("<Double-1>", lambda _event: self._edit())
        self._refresh()

    def _show_own_profile(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text="My profile", font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=24, pady=(20, 12)
        )
        with session_scope(self.session_factory) as session:
            employee = get_employee(session, self.actor, self.actor.employee_id or -1)
            values = {field.name: getattr(employee, field.name) for field in fields(EmployeeProfile)} if employee else None
        if values is None:
            ctk.CTkLabel(self, text="No employee profile is linked to this account.", text_color="#FF8585").grid(
                row=1, column=0, sticky="w", padx=24, pady=8
            )
            return
        details = ctk.CTkFrame(self, fg_color="#17243A", corner_radius=8)
        details.grid(row=1, column=0, sticky="new", padx=24, pady=12)
        for row, field in enumerate(EMPLOYEE_FIELDS):
            label = EMPLOYEE_LABELS.get(field, field.replace("_", " ").title()).replace(" *", "")
            ctk.CTkLabel(details, text=label, text_color="#9BAAC0").grid(
                row=row, column=0, sticky="w", padx=16, pady=8
            )
            ctk.CTkLabel(details, text=values.get(field) or "Not provided").grid(
                row=row, column=1, sticky="w", padx=16, pady=8
            )

    def _refresh(self) -> None:
        with session_scope(self.session_factory) as session:
            employees = list_employees(
                session,
                self.actor,
                self.search_entry.get(),
                department=self.department_entry.get().strip() or None,
                designation=self.designation_entry.get().strip() or None,
            )
            rows = [
                (
                    employee.id,
                    employee.employee_code,
                    employee.full_name,
                    employee.department,
                    employee.designation,
                    employee.work_email or "",
                    employee.work_phone or "",
                    employee.employment_status or "active",
                )
                for employee in employees
            ]
        for row in self.table.get_children():
            self.table.delete(row)
        for row in rows:
            self.table.insert("", "end", iid=str(row[0]), values=row[1:])

    def _selected_id(self) -> int | None:
        selection = self.table.selection()
        return int(selection[0]) if selection else None

    def _add(self) -> None:
        EmployeeEditor(self, self.session_factory, self.actor, None, self._refresh)

    def _edit(self) -> None:
        employee_id = self._selected_id()
        if employee_id is None:
            messagebox.showinfo("Select an employee", "Choose an employee row first.", parent=self)
            return
        with session_scope(self.session_factory) as session:
            employee = session.get(Employee, employee_id)
            data = {field.name: getattr(employee, field.name) for field in fields(EmployeeProfile)} if employee else None
        if data is None:
            messagebox.showerror("Employee unavailable", "This employee record could not be found.", parent=self)
            self._refresh()
            return
        EmployeeEditor(self, self.session_factory, self.actor, (employee_id, data), self._refresh)

    def _archive(self) -> None:
        employee_id = self._selected_id()
        if employee_id is None:
            messagebox.showinfo("Select an employee", "Choose an employee row first.", parent=self)
            return
        if not messagebox.askyesno("Archive employee", "Archive this employee record and disable its login?", parent=self):
            return
        try:
            with session_scope(self.session_factory) as session:
                archive_employee(session, self.actor, employee_id)
        except (PermissionError, LookupError) as error:
            messagebox.showerror("Could not archive employee", str(error), parent=self)
            return
        self._refresh()


class EmployeeEditor(ctk.CTkToplevel):
    def __init__(
        self,
        master: ctk.CTkFrame,
        session_factory: sessionmaker,
        actor: AuthenticatedUser,
        record: tuple[int, dict[str, str | None]] | None,
        on_saved: Callable[[], None],
    ) -> None:
        super().__init__(master)
        self.session_factory = session_factory
        self.actor = actor
        self.record = record
        self.on_saved = on_saved
        self.title("Edit employee" if record else "Add employee")
        self.geometry("560x620")
        self.minsize(480, 480)
        self.transient(master.winfo_toplevel())
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(self, text=self.title(), font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=22, pady=(18, 10)
        )
        form = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form.grid(row=1, column=0, sticky="nsew", padx=14)
        self.entries: dict[str, ctk.CTkEntry] = {}
        initial = record[1] if record else {}
        for row, field in enumerate(EMPLOYEE_FIELDS):
            ctk.CTkLabel(form, text=EMPLOYEE_LABELS.get(field, field.replace("_", " ").title())).grid(
                row=row * 2, column=0, sticky="w", padx=10, pady=(6, 0)
            )
            if field == "employment_status":
                widget = ctk.CTkComboBox(form, values=sorted(EMPLOYMENT_STATUSES))
                widget.set(initial.get(field) or "active")
            else:
                widget = ctk.CTkEntry(form)
                widget.insert(0, initial.get(field) or "")
            widget.grid(row=row * 2 + 1, column=0, sticky="ew", padx=10, pady=(2, 4))
            self.entries[field] = widget
        form.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(self, text="Save employee", command=self._save).grid(
            row=2, column=0, sticky="ew", padx=24, pady=18
        )

    def _save(self) -> None:
        values = {field: self.entries[field].get().strip() or None for field in EMPLOYEE_FIELDS}
        values["employee_code"] = values["employee_code"] or ""
        values["full_name"] = values["full_name"] or ""
        values["department"] = values["department"] or ""
        values["designation"] = values["designation"] or ""
        values["employment_status"] = values["employment_status"] or "active"
        profile = EmployeeProfile(**values)
        try:
            with session_scope(self.session_factory) as session:
                if self.record:
                    update_employee(session, self.actor, self.record[0], profile)
                else:
                    create_employee(session, self.actor, profile)
        except (ValueError, PermissionError, LookupError) as error:
            messagebox.showerror("Could not save employee", str(error), parent=self)
            return
        self.on_saved()
        self.destroy()