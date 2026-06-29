"""
Ventana principal de la aplicación.
Orquesta el menú lateral y las vistas de cada sección.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Any

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
        self._build()

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
