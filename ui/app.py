"""
Ventana principal de la aplicación.
Orquesta el menú lateral y las vistas de cada sección.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

import customtkinter as ctk

# Ajuste de path para importaciones relativas
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import COLORS, FONTS, WINDOW_WIDTH, WINDOW_HEIGHT
from services.excel_manager import ExcelManager
from services.estudiantes import EstudiantesService
from services.asistencia import AsistenciaService
from services.voluntariado import VoluntariadoService
from services.seguimiento import SeguimientoService
from services.rendimiento import RendimientoService
from services.indicadores import IndicadoresService
from services.reportes import ReportesService

from ui.menu import SidebarMenu
from ui.dashboard import DashboardView
from ui.estudiantes import EstudiantesView
from ui.seguimiento import SeguimientoView
from ui.asistencia import AsistenciaView
from ui.rendimiento import RendimientoView
from ui.voluntariado import VoluntariadoView
from ui.reportes_view import ReportesView
from ui.config_view import ConfigView


class App(ctk.CTk):
    """Ventana raíz de la aplicación."""

    def __init__(self) -> None:
        super().__init__()
        self.withdraw()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.title("Sistema Inteligente de Seguimiento — Estudiantes Becados")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(1024, 640)
        self.configure(fg_color=COLORS["bg_main"])

        # Centrar en pantalla
        self.update_idletasks()
        x = (self.winfo_screenwidth() - WINDOW_WIDTH) // 2
        y = (self.winfo_screenheight() - WINDOW_HEIGHT) // 2
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

        # Inicializar capa de servicios
        self.services: Dict[str, Any] = self._init_services()

        # Layout principal
        self._current_view = None
        self._views: Dict[str, ctk.CTkFrame] = {}
        self._perfil_window = None
        self._visible = False
        self._loading_overlay: Optional[ctk.CTkFrame] = None
        self._loading_progress: Optional[ctk.CTkProgressBar] = None
        self._loading_show_after_id: Optional[str] = None
        self._loading_hide_after_id: Optional[str] = None
        self._loading_started_at: Optional[float] = None
        self._minimum_loading_visible = 2000
        self._build()

    def _create_loading_overlay(self) -> None:
        if self._loading_overlay and self._loading_overlay.winfo_exists():
            return

        overlay = ctk.CTkFrame(self, fg_color=COLORS["bg_sidebar"], corner_radius=0)
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        overlay.lower()
        overlay.bind("<Button-1>", lambda event: "break")
        overlay.bind("<ButtonRelease-1>", lambda event: "break")
        overlay.bind("<Key>", lambda event: "break")

        card = ctk.CTkFrame(
            overlay,
            fg_color=COLORS["bg_card"],
            corner_radius=18,
            border_width=1,
            border_color=COLORS["border"],
            width=450,
            height=240,
        )
        card.place(relx=0.5, rely=0.5, anchor="center")

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(
            content,
            text="Cargando información...",
            font=FONTS["heading_md"],
            text_color=COLORS["text_primary"],
        ).pack(pady=(0, 10))

        ctk.CTkLabel(
            content,
            text="Espere un momento, por favor",
            font=FONTS["body"],
            text_color=COLORS["text_secondary"],
        ).pack(pady=(0, 18))

        progress = ctk.CTkProgressBar(content, mode="indeterminate", width=220)
        progress.pack(fill="x", pady=(0, 18))

        self._loading_overlay = overlay
        self._loading_progress = progress
        self._loading_title = None
        self._loading_subtitle = None

    def show_loading(self, immediate: bool = False) -> None:
        if self._loading_show_after_id and self.after_info(self._loading_show_after_id):
            try:
                self.after_cancel(self._loading_show_after_id)
            except Exception:
                pass
            self._loading_show_after_id = None

        if immediate:
            self._show_loading_overlay()
            return

        self._loading_show_after_id = self.after(450, self._show_loading_overlay)

    def _show_loading_overlay(self) -> None:
        self._loading_show_after_id = None
        self._create_loading_overlay()
        if self._loading_overlay:
            self._loading_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._loading_overlay.lift()
        if self._loading_progress:
            self._loading_progress.start()
        self._loading_started_at = time.time()

    def _hide_loading_overlay(self) -> None:
        self._loading_hide_after_id = None
        if self._loading_progress:
            try:
                self._loading_progress.stop()
            except Exception:
                pass
        if self._loading_overlay and self._loading_overlay.winfo_exists():
            self._loading_overlay.place_forget()
        self._loading_started_at = None

    def hide_loading(self) -> None:
        if self._loading_show_after_id and self.after_info(self._loading_show_after_id):
            try:
                self.after_cancel(self._loading_show_after_id)
            except Exception:
                pass
            self._loading_show_after_id = None

        if self._loading_hide_after_id and self.after_info(self._loading_hide_after_id):
            try:
                self.after_cancel(self._loading_hide_after_id)
            except Exception:
                pass
            self._loading_hide_after_id = None

        if self._loading_overlay and self._loading_overlay.winfo_exists():
            if self._loading_started_at is None:
                self._hide_loading_overlay()
                return

            elapsed_ms = int((time.time() - self._loading_started_at) * 1000)
            wait_ms = self._minimum_loading_visible - elapsed_ms
            if wait_ms > 0:
                self._loading_hide_after_id = self.after(wait_ms, self._hide_loading_overlay)
                return

        self._hide_loading_overlay()

    # ── Servicios ─────────────────────────────────────────────────────────────

    def _init_services(self) -> Dict[str, Any]:
        excel = ExcelManager()
        asistencia = AsistenciaService(excel)
        voluntariado = VoluntariadoService(excel)
        seguimiento = SeguimientoService(excel)
        rendimiento = RendimientoService(excel)
        indicadores = IndicadoresService(asistencia, voluntariado, seguimiento, rendimiento)
        return {
            "excel": excel,
            "estudiantes": EstudiantesService(excel),
            "asistencia": asistencia,
            "voluntariado": voluntariado,
            "seguimiento": seguimiento,
            "rendimiento": rendimiento,
            "indicadores": indicadores,
            "reportes": ReportesService(),
        }

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        # Contenedor raíz en fila: sidebar | contenido
        self._root_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_main"])
        self._root_frame.pack(fill="both", expand=True)

        # Menú lateral
        self._sidebar = SidebarMenu(self._root_frame, on_navigate=self._navigate)
        self._sidebar.pack(side="left", fill="y")

        # Área de contenido
        self._content_area = ctk.CTkFrame(
            self._root_frame,
            fg_color=COLORS["bg_main"],
            corner_radius=0,
        )
        self._content_area.pack(side="left", fill="both", expand=True)

        # Mostrar dashboard por defecto
        self._navigate("dashboard")

    def _show(self) -> None:
        if self._visible:
            return
        self.update_idletasks()
        self.deiconify()
        self.lift()
        self._visible = True

    def _navigate(self, key: str) -> None:
        """Muestra la vista correspondiente al key de navegación."""
        # Ocultar vista actual
        if self._current_view:
            self._current_view.pack_forget()

        # Crear vista si no existe (lazy init)
        if key not in self._views:
            self._views[key] = self._create_view(key)

        view = self._views[key]
        view.pack(fill="both", expand=True)
        self._current_view = view

        # Refrescar si la vista tiene el método
        if hasattr(view, "refresh"):
            if key == "dashboard" and not self._visible:
                view.refresh(on_complete=self._show)
            elif key == "asistencia":
                view.refresh(immediate=True)
            else:
                view.refresh()

    def _create_view(self, key: str) -> ctk.CTkFrame:
        """Instancia la vista correspondiente."""
        factory = {
            "dashboard": lambda: DashboardView(self._content_area, self),
            "estudiantes": lambda: EstudiantesView(self._content_area, self),
            "seguimiento": lambda: SeguimientoView(self._content_area, self),
            "asistencia": lambda: AsistenciaView(self._content_area, self),
            "rendimiento": lambda: RendimientoView(self._content_area, self),
            "voluntariado": lambda: VoluntariadoView(self._content_area, self),
            "reportes": lambda: ReportesView(self._content_area, self),
            "config": lambda: ConfigView(self._content_area, self),
        }
        creator = factory.get(key)
        if not creator:
            return ctk.CTkFrame(self._content_area, fg_color=COLORS["bg_main"])
        view = creator()
        view.place_forget()  # aún no visible
        return view

    # ── API pública para sub-vistas ───────────────────────────────────────────

    def abrir_perfil(self, estudiante_id: int) -> None:
        """Abre la ventana de perfil de un estudiante."""
        from ui.perfil import PerfilEstudianteView
        self._perfil_window = PerfilEstudianteView(self, estudiante_id)
