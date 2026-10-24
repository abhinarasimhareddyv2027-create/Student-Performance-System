from collections.abc import Callable

import customtkinter as ctk
from sqlalchemy.orm import sessionmaker

from services.auth_service import AuthenticatedUser
from services.dashboard_service import get_dashboard_summary


class DashboardScreen(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTk,
        session_factory: sessionmaker,
        actor: AuthenticatedUser,
        on_logout: Callable[[], None],
        on_open_students: Callable[[], None],
        on_open_employees: Callable[[], None],
    ) -> None:
        super().__init__(master, fg_color="#101827")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#121D2E")
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        ctk.CTkLabel(sidebar, text="SPMS", font=ctk.CTkFont(size=23, weight="bold")).pack(
            padx=24, pady=(30, 28), anchor="w"
        )
        ctk.CTkLabel(sidebar, text="Overview", text_color="#66D1C4").pack(
            padx=24, pady=8, anchor="w"
        )
        if actor.role in {"admin", "teacher"}:
            ctk.CTkButton(
                sidebar,
                text="Students",
                command=on_open_students,
                fg_color="transparent",
                anchor="w",
                hover_color="#202E43",
            ).pack(padx=16, pady=(8, 0), fill="x")
        if actor.role in {"admin", "employee"}:
            ctk.CTkButton(
                sidebar,
                text="Employees" if actor.role == "admin" else "My profile",
                command=on_open_employees,
                fg_color="transparent",
                anchor="w",
                hover_color="#202E43",
            ).pack(padx=16, pady=(4, 0), fill="x")
        ctk.CTkLabel(sidebar, text=f"{actor.username}  ·  {actor.role.title()}", text_color="#9BAAC0").pack(
            side="bottom", padx=24, pady=(8, 18), anchor="w"
        )
        ctk.CTkButton(
            sidebar,
            text="Sign out",
            command=on_logout,
            fg_color="transparent",
            border_width=1,
            border_color="#45556B",
            hover_color="#202E43",
        ).pack(side="bottom", padx=20, pady=16, fill="x")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=1, sticky="nsew", padx=36, pady=32)
        content.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(content, text="Overview", font=ctk.CTkFont(size=28, weight="bold")).grid(
            row=0, column=0, sticky="w"
        )
        ctk.CTkLabel(content, text="Current records", text_color="#9BAAC0").grid(
            row=1, column=0, sticky="w", pady=(4, 24)
        )

        with session_factory() as session:
            summary = get_dashboard_summary(session, actor)

        self._metric_card(content, "Students", summary.total_students, 0)
        self._metric_card(content, "Employees", summary.total_employees, 1)

    @staticmethod
    def _metric_card(parent: ctk.CTkFrame, label: str, value: int | None, column: int) -> None:
        card = ctk.CTkFrame(parent, corner_radius=8, fg_color="#17243A")
        card.grid(row=2, column=column, sticky="ew", padx=(0 if column == 0 else 8, 8 if column == 0 else 0))
        ctk.CTkLabel(card, text=label, text_color="#AAB7C9").pack(anchor="w", padx=22, pady=(20, 4))
        display_value = str(value) if value is not None else "Restricted"
        ctk.CTkLabel(card, text=display_value, font=ctk.CTkFont(size=34, weight="bold")).pack(
            anchor="w", padx=22, pady=(0, 20)
        )