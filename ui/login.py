from collections.abc import Callable

import customtkinter as ctk
from sqlalchemy.orm import sessionmaker

from database.connection import session_scope
from services.auth_service import AuthenticatedUser, authenticate_user


class LoginScreen(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTk,
        session_factory: sessionmaker,
        on_authenticated: Callable[[AuthenticatedUser], None],
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self.session_factory = session_factory
        self.on_authenticated = on_authenticated
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        panel = ctk.CTkFrame(self, width=420, corner_radius=12, fg_color="#17243A")
        panel.grid(row=0, column=0, padx=24, pady=24)
        panel.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(panel, text="Performance System", font=ctk.CTkFont(size=25, weight="bold")).grid(
            row=0, column=0, padx=32, pady=(34, 6), sticky="w"
        )
        ctk.CTkLabel(panel, text="Sign in", text_color="#9BAAC0").grid(
            row=1, column=0, padx=32, pady=(0, 22), sticky="w"
        )

        self.username_entry = ctk.CTkEntry(panel, placeholder_text="Username", height=42)
        self.username_entry.grid(row=2, column=0, padx=32, pady=8, sticky="ew")
        self.password_entry = ctk.CTkEntry(panel, placeholder_text="Password", show="*", height=42)
        self.password_entry.grid(row=3, column=0, padx=32, pady=8, sticky="ew")
        self.password_entry.bind("<Return>", self._submit)
        self.error_label = ctk.CTkLabel(panel, text="", text_color="#FF8585", wraplength=350)
        self.error_label.grid(row=4, column=0, padx=32, pady=(4, 0), sticky="w")
        ctk.CTkButton(
            panel,
            text="Sign in",
            command=self._submit,
            height=42,
            fg_color="#128C83",
            hover_color="#0F746D",
        ).grid(row=5, column=0, padx=32, pady=(14, 34), sticky="ew")
        self.username_entry.focus_set()

    def _submit(self, _event: object = None) -> None:
        with session_scope(self.session_factory) as session:
            actor = authenticate_user(
                session,
                self.username_entry.get(),
                self.password_entry.get(),
            )
        if actor is None:
            self.error_label.configure(text="Sign-in failed. Check your details or contact an administrator.")
            self.password_entry.delete(0, "end")
            return

        self.error_label.configure(text="")
        self.on_authenticated(actor)