from collections.abc import Callable
from dataclasses import fields
from tkinter import messagebox, ttk

import customtkinter as ctk
from sqlalchemy.orm import sessionmaker

from database.connection import session_scope
from database.models import Student
from services.auth_service import AuthenticatedUser
from services.student_service import (
    StudentProfile,
    archive_student,
    create_student,
    list_students,
    update_student,
)


STUDENT_FIELDS = (
    "register_number",
    "admission_number",
    "full_name",
    "date_of_birth",
    "email",
    "phone",
    "address",
    "guardian_name",
    "guardian_contact",
    "course",
    "department",
    "branch",
    "academic_year",
    "current_semester",
    "section",
    "admission_date",
    "enrollment_status",
)
STUDENT_LABELS = {
    "register_number": "Register number *",
    "admission_number": "Admission number",
    "full_name": "Full name *",
    "date_of_birth": "Date of birth (YYYY-MM-DD)",
    "guardian_contact": "Guardian contact",
    "current_semester": "Current semester",
    "admission_date": "Admission date (YYYY-MM-DD)",
    "enrollment_status": "Enrollment status",
}


class StudentScreen(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkToplevel, session_factory: sessionmaker, actor: AuthenticatedUser) -> None:
        super().__init__(master, fg_color="#101827")
        self.session_factory = session_factory
        self.actor = actor
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        heading = ctk.CTkFrame(self, fg_color="transparent")
        heading.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 8))
        ctk.CTkLabel(heading, text="Students", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        ctk.CTkButton(heading, text="Add student", command=self._add, width=120).pack(side="right")

        filters = ctk.CTkFrame(self, fg_color="transparent")
        filters.grid(row=1, column=0, sticky="ew", padx=24, pady=8)
        self.search_entry = ctk.CTkEntry(filters, placeholder_text="Search name or register number", width=250)
        self.search_entry.pack(side="left", padx=(0, 8))
        self.filter_entries = {}
        for field in ("course", "department", "academic_year", "current_semester", "section"):
            entry = ctk.CTkEntry(filters, placeholder_text=field.replace("_", " ").title(), width=125)
            entry.pack(side="left", padx=4)
            self.filter_entries[field] = entry
        self.search_entry.bind("<Return>", lambda _event: self._refresh())
        ctk.CTkButton(filters, text="Search", command=self._refresh, width=76).pack(side="left", padx=8)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 8))
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
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        columns = ("register", "name", "course", "department", "year", "semester", "section", "status")
        self.table = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        for key, title, width in zip(columns, ("Register", "Full name", "Course", "Department", "Year", "Semester", "Section", "Status"), (110, 190, 160, 140, 80, 90, 80, 100)):
            self.table.heading(key, text=title)
            self.table.column(key, width=width, minwidth=65, stretch=True)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.table.bind("<Double-1>", lambda _event: self._edit())
        self._refresh()

    def _refresh(self) -> None:
        filters = {key: entry.get().strip() or None for key, entry in self.filter_entries.items()}
        with session_scope(self.session_factory) as session:
            students = list_students(session, self.actor, self.search_entry.get(), **filters)
            rows = [
                (
                    student.id,
                    student.register_number,
                    student.full_name,
                    student.course or "",
                    student.department or "",
                    student.academic_year or "",
                    student.current_semester or "",
                    student.section or "",
                    student.enrollment_status or "active",
                )
                for student in students
            ]
        for row in self.table.get_children():
            self.table.delete(row)
        for row in rows:
            self.table.insert("", "end", iid=str(row[0]), values=row[1:])

    def _selected_id(self) -> int | None:
        selection = self.table.selection()
        return int(selection[0]) if selection else None

    def _add(self) -> None:
        StudentEditor(self, self.session_factory, self.actor, None, self._refresh)

    def _edit(self) -> None:
        student_id = self._selected_id()
        if student_id is None:
            messagebox.showinfo("Select a student", "Choose a student row first.", parent=self)
            return
        with session_scope(self.session_factory) as session:
            student = session.get(Student, student_id)
            data = {field.name: getattr(student, field.name) for field in fields(StudentProfile)} if student else None
        if data is None:
            messagebox.showerror("Student unavailable", "This student record could not be found.", parent=self)
            self._refresh()
            return
        StudentEditor(self, self.session_factory, self.actor, (student_id, data), self._refresh)

    def _archive(self) -> None:
        student_id = self._selected_id()
        if student_id is None:
            messagebox.showinfo("Select a student", "Choose a student row first.", parent=self)
            return
        if not messagebox.askyesno("Archive student", "Archive this student record?", parent=self):
            return
        try:
            with session_scope(self.session_factory) as session:
                archive_student(session, self.actor, student_id)
        except (PermissionError, LookupError) as error:
            messagebox.showerror("Could not archive student", str(error), parent=self)
            return
        self._refresh()


class StudentEditor(ctk.CTkToplevel):
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
        self.title("Edit student" if record else "Add student")
        self.geometry("560x700")
        self.minsize(480, 500)
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
        for row, field in enumerate(STUDENT_FIELDS):
            ctk.CTkLabel(form, text=STUDENT_LABELS.get(field, field.replace("_", " ").title())).grid(
                row=row * 2, column=0, sticky="w", padx=10, pady=(6, 0)
            )
            if field == "enrollment_status":
                widget = ctk.CTkComboBox(
                    form,
                    values=["active", "withdrawn", "graduated", "suspended", "archived"],
                )
                widget.set(initial.get(field) or "active")
            else:
                widget = ctk.CTkEntry(form)
                widget.insert(0, initial.get(field) or "")
            widget.grid(row=row * 2 + 1, column=0, sticky="ew", padx=10, pady=(2, 4))
            self.entries[field] = widget
        form.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(self, text="Save student", command=self._save).grid(
            row=2, column=0, sticky="ew", padx=24, pady=18
        )

    def _save(self) -> None:
        values = {
            field: self.entries[field].get().strip() or None
            for field in STUDENT_FIELDS
        }
        values["register_number"] = values["register_number"] or ""
        values["full_name"] = values["full_name"] or ""
        values["enrollment_status"] = values["enrollment_status"] or "active"
        profile = StudentProfile(**values)
        try:
            with session_scope(self.session_factory) as session:
                if self.record:
                    update_student(session, self.actor, self.record[0], profile)
                else:
                    create_student(session, self.actor, profile)
        except (ValueError, PermissionError, LookupError) as error:
            messagebox.showerror("Could not save student", str(error), parent=self)
            return
        self.on_saved()
        self.destroy()