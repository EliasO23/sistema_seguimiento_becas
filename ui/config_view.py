"""Vista de configuración del sistema."""

from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter as ctk

from config import COLORS, FONTS, HORAS_VOLUNTARIADO_REQUERIDAS, PROMEDIO_MINIMO, CONTENT_MAX_WIDTH
from ui.components.cards import ActionButton, SectionHeader

if TYPE_CHECKING:
    from ui.app import App


class ConfigView(ctk.CTkFrame):
    """Panel de configuración y parámetros del sistema."""

    def __init__(self, master, app: "App", **kwargs) -> None:
        super().__init__(master, fg_color=COLORS["bg_main"], **kwargs)
        self._app = app
        self._build()

    def _build(self) -> None:
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], height=104, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkFrame(header, height=4, fg_color=COLORS["primary"], corner_radius=0).pack(fill="x")
        ctk.CTkLabel(
            header,
            text="Configuración del Sistema",
            font=("Segoe UI", 22, "bold"),
            text_color=COLORS["text_primary"],
        ).pack(anchor="w", padx=24, pady=(18, 4))
        ctk.CTkLabel(
            header,
            text="Ajusta los parámetros clave del sistema desde un panel limpio, organizado y fácil de interpretar.",
            font=FONTS["body"],
            text_color=COLORS["text_secondary"],
        ).pack(anchor="w", padx=24, pady=(0, 18))

        # Contenedor principal sin scroll, porque el contenido cabe en la altura disponible
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=24, pady=18)
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(0, weight=1)

        content = ctk.CTkFrame(outer, fg_color="transparent")
        content.pack(fill="both", expand=True, pady=(0, 18))
        content.grid_columnconfigure(0, weight=0)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)

        menu = ctk.CTkFrame(content, fg_color=COLORS["bg_card"], corner_radius=18, border_width=1, border_color=COLORS["border"], width=240)
        menu.grid(row=0, column=0, sticky="ns", padx=(0, 16), pady=(0, 0))
        menu.grid_propagate(False)

        ctk.CTkLabel(menu, text="Opciones", font=("Segoe UI", 15, "bold"), text_color=COLORS["text_primary"]).pack(anchor="w", padx=16, pady=(16, 10))
        self._menu_buttons = {}
        menu_items = [
            ("params", "Parametro"),
            ("riesgo", "Riesgo"),
            ("sistema", "Sistema"),
        ]
        for key, title in menu_items:
            btn = ctk.CTkButton(
                menu,
                text=title,
                fg_color="transparent",
                hover=False,
                text_color=COLORS["text_primary"],
                height=40,
                corner_radius=0,
                border_width=0,
                anchor="w",
                border_spacing=16,
                command=lambda k=key: self._on_menu_select(k),
            )
            btn.pack(fill="x", padx=2, pady=4)
            self._menu_buttons[key] = btn

        main = ctk.CTkFrame(content, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_rowconfigure(0, weight=1)
        main.grid_columnconfigure(0, weight=1)

        # Contenedor para mostrar una sola sección activa a la vez
        section_container = ctk.CTkFrame(main, fg_color="transparent")
        section_container.grid(row=0, column=0, sticky="nsew", pady=(0, 12))
        section_container.grid_rowconfigure(0, weight=1)
        section_container.grid_columnconfigure(0, weight=1)

        # Secciones como paneles independientes
        self._sections = {}

        # Parámetros de negocio (panel)
        params_panel = ctk.CTkFrame(section_container, fg_color=COLORS["bg_card"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        SectionHeader(params_panel, "⚙️ Parámetros de Negocio", "Controla los límites y reglas del seguimiento.").pack(fill="x", padx=16, pady=(6, 8))

        params = [
            ("Horas de Voluntariado Requeridas", str(HORAS_VOLUNTARIADO_REQUERIDAS), "horas"),
            ("Promedio Mínimo Académico", str(PROMEDIO_MINIMO), "puntos"),
            ("Asistencia Mínima Requerida", "75", "%"),
            ("Días sin seguimiento (alerta)", "30", "días"),
        ]
        self._param_entries = {}
        for label, default, unit in params:
            row = ctk.CTkFrame(params_panel, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=6)
            ctk.CTkLabel(row, text=label, font=FONTS["body"], text_color=COLORS["text_primary"], width=260, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(row, width=120, height=32, font=FONTS["body"])
            entry.insert(0, default)
            entry.pack(side="left", padx=(0, 8))
            ctk.CTkLabel(row, text=unit, font=FONTS["body_sm"], text_color=COLORS["text_secondary"]).pack(side="left")
            self._param_entries[label] = entry
        self._sections["params"] = params_panel

        # Pesos del índice de riesgo
        pesos_panel = ctk.CTkFrame(section_container, fg_color=COLORS["bg_card"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        SectionHeader(pesos_panel, "📊 Pesos del Índice de Riesgo", "Define la importancia de cada factor en la evaluación.").pack(fill="x", padx=16, pady=(6, 8))

        pesos = [
            ("Asistencia", "40"),
            ("Promedio Académico", "30"),
            ("Voluntariado", "20"),
            ("Seguimiento", "10"),
        ]
        for label, default in pesos:
            row = ctk.CTkFrame(pesos_panel, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=6)
            ctk.CTkLabel(row, text=label, font=FONTS["body"], text_color=COLORS["text_primary"], width=220, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(row, width=100, height=32, font=FONTS["body"])
            entry.insert(0, default)
            entry.pack(side="left", padx=(0, 8))
            ctk.CTkLabel(row, text="%", font=FONTS["body_sm"], text_color=COLORS["text_secondary"]).pack(side="left")
        self._sections["riesgo"] = pesos_panel

        # Info del sistema
        info_panel = ctk.CTkFrame(section_container, fg_color=COLORS["bg_card"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        SectionHeader(info_panel, "ℹ️ Información del Sistema", "Detalles técnicos del entorno actual.").pack(fill="x", padx=16, pady=(6, 8))

        info_items = [
            ("Versión", "1.0.0"),
            ("Motor de base de datos", "Excel (OpenPyXL)"),
            ("Framework UI", "CustomTkinter"),
            ("Visualización", "Matplotlib"),
            ("Reportes", "ReportLab"),
            ("Análisis de datos", "Pandas / NumPy"),
            ("Hecho por", "AEME Tech"),
            ("Desarrollador Backend", "Manuel Alfredo Lara Guardado"),
            ("Desarrollador Backend", "Elias Antonio Oliva Calderon"),
            ("Desarrollador Frontend", "Emerson Eli Mendoza Lemus"),
        ]
        for label, value in info_items:
            row = ctk.CTkFrame(info_panel, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=6)
            ctk.CTkLabel(row, text=f"{label}:", font=FONTS["body_sm"], text_color=COLORS["text_secondary"], width=220, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=value, font=FONTS["body"], text_color=COLORS["text_primary"]).pack(side="left")
        self._sections["sistema"] = info_panel

        footer = ctk.CTkFrame(main, fg_color="transparent")
        footer.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        ActionButton(footer, "💾 Guardar Configuración", command=self._guardar).pack(side="left")
        self._msg = ctk.CTkLabel(footer, text="", font=FONTS["body_sm"], text_color=COLORS["success"])
        self._msg.pack(side="left", padx=(12, 0))

        # Inicializar visibilidad: mostrar la primera opción
        self._on_menu_select("params")

    def _on_menu_select(self, key: str) -> None:
        # esconder todas las secciones
        for k, widget in list(self._sections.items()):
            try:
                widget.pack_forget()
            except Exception:
                pass
            try:
                widget.grid_forget()
            except Exception:
                pass

        # mostrar la solicitada
        if key in self._sections:
            self._sections[key].grid(row=0, column=0, sticky="nsew", pady=(0, 12))

        # actualizar estilo de botones si existen
        for mk, btn in getattr(self, "_menu_buttons", {}).items():
            if mk == key:
                btn.configure(fg_color=COLORS["primary_light"], text_color=COLORS["primary_dark"])
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_primary"])

    def _adjust_inner_width(self, event, inner_frame) -> None:
        try:
            max_w = CONTENT_MAX_WIDTH
            margin = 64
            avail = max(320, event.width - margin)
            new_w = min(max_w, avail)
            if inner_frame.winfo_width() != new_w:
                inner_frame.configure(width=new_w)
        except Exception:
            pass

    def _guardar(self) -> None:
        self._msg.configure(
            text="✅ Configuración guardada. Reinicia la aplicación para aplicar cambios.",
            text_color=COLORS["success"],
        )
