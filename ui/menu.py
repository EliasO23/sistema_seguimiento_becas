"""Menú lateral de navegación."""

from __future__ import annotations
from typing import Callable, Dict

import customtkinter as ctk
from config import COLORS, FONTS, SIDEBAR_WIDTH


class SidebarMenu(ctk.CTkFrame):
    """Menú lateral con iconos y navegación."""

    ITEMS = [
        ("🏠", "Dashboard", "dashboard"),
        ("👥", "Estudiantes", "estudiantes"),
        ("📋", "Seguimiento", "seguimiento"),
        ("✅", "Asistencia", "asistencia"),
        ("📈", "Rendimiento", "rendimiento"),
        ("🤝", "Voluntariado", "voluntariado"),
        ("📊", "Reportes", "reportes"),
        ("⚙️", "Configuración", "config"),
    ]

    def __init__(self, master, on_navigate: Callable[[str], None], **kwargs) -> None:
        super().__init__(
            master,
            fg_color=COLORS["bg_sidebar"],
            width=SIDEBAR_WIDTH,
            corner_radius=0,
            **kwargs,
        )
        self._on_navigate = on_navigate
        self._active: str = "dashboard"
        self._buttons: Dict[str, ctk.CTkButton] = {}
        self._build()

    def _build(self) -> None:
        self.pack_propagate(False)

        # Logo / sistema
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(20, 16), padx=16)

        ctk.CTkLabel(
            logo_frame, text="🎓",
            font=("Segoe UI Emoji", 32),
            text_color=COLORS["primary"],
        ).pack()
        ctk.CTkLabel(
            logo_frame, text="Sistema Becados",
            font=FONTS["heading_sm"],
            text_color=COLORS["text_white"],
        ).pack()
        ctk.CTkLabel(
            logo_frame, text="Ministerio de Educación",
            font=FONTS["caption"],
            text_color=COLORS["text_light"],
        ).pack()

        # Separador
        ctk.CTkFrame(
            self, height=1,
            fg_color=COLORS["bg_sidebar_hover"],
        ).pack(fill="x", padx=16, pady=(0, 12))

        # Etiqueta sección
        ctk.CTkLabel(
            self, text="NAVEGACIÓN",
            font=("Segoe UI", 9, "bold"),
            text_color=COLORS["text_light"],
        ).pack(anchor="w", padx=20, pady=(0, 8))

        # Botones de menú
        for icon, label, key in self.ITEMS:
            btn = ctk.CTkButton(
                self,
                text=f"  {icon}  {label}",
                anchor="w",
                height=44,
                corner_radius=8,
                fg_color="transparent",
                hover_color=COLORS["bg_sidebar_hover"],
                text_color=COLORS["text_light"],
                font=FONTS["body"],
                command=lambda k=key: self._navigate(k),
            )
            btn.pack(fill="x", padx=12, pady=2)
            self._buttons[key] = btn

        # Fondo restante
        ctk.CTkFrame(self, fg_color="transparent").pack(fill="both", expand=True)

        # Pie del menú
        ctk.CTkFrame(self, height=1, fg_color=COLORS["bg_sidebar_hover"]).pack(fill="x", padx=16)
        ctk.CTkLabel(
            self,
            text="© 2026 Sistema Becados",
            font=FONTS["caption"],
            text_color=COLORS["text_light"],
        ).pack(pady=12)

        # Activar dashboard por defecto
        self._set_active("dashboard")

    def _navigate(self, key: str) -> None:
        self._set_active(key)
        self._on_navigate(key)

    def _set_active(self, key: str) -> None:
        for k, btn in self._buttons.items():
            if k == key:
                btn.configure(
                    fg_color=COLORS["primary"],
                    text_color=COLORS["text_white"],
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS["text_light"],
                )
        self._active = key

    def set_active(self, key: str) -> None:
        self._set_active(key)
