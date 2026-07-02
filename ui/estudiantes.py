"""Vista de gestión de estudiantes."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Optional

import customtkinter as ctk

from config import COLORS, FONTS, UNIVERSIDADES, CARRERAS, ESTADOS_ESTUDIANTE
from services.estudiantes import Estudiante
from ui.components.cards import (
    SectionHeader, SearchBar, ActionButton, DataTable, RiskBadge, KPICard
)

if TYPE_CHECKING:
    from ui.app import App


class EstudiantesView(ctk.CTkFrame):
    """Pantalla de listado y CRUD de estudiantes."""

    COLUMNS = ["ID", "Código", "Nombre", "Universidad", "Carrera", "Ciclo", "Monitor", "Estado"]

    def __init__(self, master, app: "App", **kwargs) -> None:
        super().__init__(master, fg_color=COLORS["bg_main"], **kwargs)
        self._app = app
        self._selected_id: Optional[int] = None
        self._all_rows: list = []
        self._build()

    def _build(self) -> None:
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], height=64, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="Gestión de Estudiantes",
                     font=FONTS["heading_lg"],
                     text_color=COLORS["text_primary"]).pack(side="left", padx=24, pady=16)

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right", padx=24, pady=12)

        ActionButton(btn_frame, "➕ Nuevo", command=self._abrir_formulario).pack(side="left", padx=4)
        ActionButton(btn_frame, "✏️ Editar", style="secondary",
                     command=self._editar_seleccionado).pack(side="left", padx=4)
        ActionButton(btn_frame, "🗑 Eliminar", style="danger",
                     command=self._eliminar_seleccionado).pack(side="left", padx=4)
        ActionButton(btn_frame, "👁 Perfil", style="ghost",
                     command=self._ver_perfil).pack(side="left", padx=4)

        # Contenido
        content = ctk.CTkFrame(self, fg_color=COLORS["bg_main"])
        content.pack(fill="both", expand=True, padx=20, pady=16)

        stats = ctk.CTkFrame(content, fg_color="transparent")
        stats.pack(fill="x", pady=(0, 14))
        stats.grid_columnconfigure(0, weight=1)
        stats.grid_columnconfigure(1, weight=1)
        stats.grid_columnconfigure(2, weight=1)

        self._active_card = KPICard(
            stats,
            "Activos",
            "0",
            subtitle="Estudiantes activos",
            icon="✅",
            accent_color=COLORS["success"],
        )
        self._active_card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        self._retired_card = KPICard(
            stats,
            "Retirados",
            "0",
            subtitle="Estudiantes retirados",
            icon="↩️",
            accent_color=COLORS["warning"],
        )
        self._retired_card.grid(row=0, column=1, padx=8, sticky="nsew")

        self._suspended_card = KPICard(
            stats,
            "Suspendidos",
            "0",
            subtitle="Estudiantes suspendidos",
            icon="⏸️",
            accent_color=COLORS["danger"],
        )
        self._suspended_card.grid(row=0, column=2, padx=(8, 0), sticky="nsew")

        # Barra de filtros
        filter_bar = ctk.CTkFrame(content, fg_color="transparent")
        filter_bar.pack(fill="x", pady=(0, 12))

        self._search = SearchBar(filter_bar, placeholder="Buscar por nombre, código, universidad...",
                                 command=self._on_search)
        self._search.pack(side="left", fill="x", expand=True, padx=(0, 12))

        ctk.CTkLabel(filter_bar, text="Estado:",
                     font=FONTS["body_sm"],
                     text_color=COLORS["text_secondary"]).pack(side="left", padx=(0, 4))
        self._filtro_estado = ctk.CTkComboBox(
            filter_bar,
            values=["Todos"] + ESTADOS_ESTUDIANTE,
            width=130, height=36,
            font=FONTS["body_sm"],
            command=self._on_filtro,
        )
        self._filtro_estado.set("Todos")
        self._filtro_estado.pack(side="left")

        # Tabla
        table_frame = ctk.CTkFrame(content, fg_color=COLORS["bg_card"],
                                   corner_radius=12, border_width=1, border_color=COLORS["border"])
        table_frame.pack(fill="both", expand=True)

        self._table = DataTable(table_frame, columns=self.COLUMNS, height=480)
        self._table.pack(fill="both", expand=True, padx=4, pady=4)

        # Barra de estado
        self._status_lbl = ctk.CTkLabel(content, text="",
                                         font=FONTS["caption"],
                                         text_color=COLORS["text_secondary"])
        self._status_lbl.pack(anchor="w", pady=(8, 0))

        self.refresh()

    def refresh(self) -> None:
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self) -> None:
        try:
            estudiantes = self._app.services["estudiantes"].listar_todos()
            self._all_rows = [
                [
                    str(e.id or ""),
                    e.codigo,
                    e.nombre_completo,
                    e.universidad[:30] if e.universidad else "",
                    e.carrera[:25] if e.carrera else "",
                    e.ciclo,
                    e.monitor[:20] if e.monitor else "",
                    e.estado,
                ]
                for e in estudiantes
            ]
            estadisticas = {"Activo": 0, "Retirado": 0, "Suspendido": 0}
            for estudiante in estudiantes:
                estadisticas[estudiante.estado] = estadisticas.get(estudiante.estado, 0) + 1
            self.after(0, lambda: self._render_stats(self._all_rows, len(estudiantes), estadisticas))
        except Exception as exc:
            self.after(0, lambda exc=exc: self._status_lbl.configure(text=f"Error: {exc}", text_color=COLORS["danger"]))

    def _render_stats(self, rows: list, total: int, estadisticas: dict) -> None:
        self._refresh_table(rows, total)
        self._active_card.update_value(str(estadisticas.get("Activo", 0)))
        self._retired_card.update_value(str(estadisticas.get("Retirado", 0)))
        self._suspended_card.update_value(str(estadisticas.get("Suspendido", 0)))

    def _refresh_table(self, rows: list, total: int) -> None:
        self._table.load_data(rows, on_select=self._on_row_select)
        shown = self._table.rendered_rows
        extra = f" — mostrando {shown} por rendimiento" if shown < total else ""
        self._status_lbl.configure(
            text=f"{total} estudiante(s) encontrado(s){extra}",
            text_color=COLORS["text_secondary"],
        )

    def _on_row_select(self, row_idx: int, row_data: list) -> None:
        try:
            self._selected_id = int(row_data[0])
        except (ValueError, IndexError):
            self._selected_id = None

    def _on_search(self, query: str) -> None:
        if not query:
            self._refresh_table(self._all_rows, len(self._all_rows))
            return
        q = query.lower()
        filtered = [r for r in self._all_rows if any(q in str(c).lower() for c in r)]
        self._refresh_table(filtered, len(filtered))

    def _on_filtro(self, estado: str) -> None:
        if estado == "Todos":
            self._refresh_table(self._all_rows, len(self._all_rows))
        else:
            filtered = [r for r in self._all_rows if r[7] == estado]
            self._refresh_table(filtered, len(filtered))

    def _abrir_formulario(self, estudiante: Optional[Estudiante] = None) -> None:
        FormularioEstudiante(self, estudiante=estudiante, on_save=self._on_save)

    def _editar_seleccionado(self) -> None:
        if not self._selected_id:
            self._mostrar_aviso("Selecciona un estudiante primero.")
            return
        est = self._app.services["estudiantes"].obtener_por_id(self._selected_id)
        if est:
            self._abrir_formulario(est)

    def _eliminar_seleccionado(self) -> None:
        if not self._selected_id:
            self._mostrar_aviso("Selecciona un estudiante primero.")
            return
        dialogo = ctk.CTkToplevel(self)
        dialogo.title("Confirmar eliminación")
        dialogo.geometry("360x160")
        dialogo.grab_set()
        ctk.CTkLabel(dialogo, text="¿Eliminar este estudiante?\nEsta acción no se puede deshacer.",
                     font=FONTS["body"], text_color=COLORS["text_primary"]).pack(pady=24)
        btn_frame = ctk.CTkFrame(dialogo, fg_color="transparent")
        btn_frame.pack()

        def confirmar():
            self._app.services["estudiantes"].eliminar(self._selected_id)
            self._selected_id = None
            dialogo.destroy()
            self.refresh()

        ActionButton(btn_frame, "Eliminar", style="danger", command=confirmar).pack(side="left", padx=8)
        ActionButton(btn_frame, "Cancelar", style="secondary", command=dialogo.destroy).pack(side="left", padx=8)

    def _ver_perfil(self) -> None:
        if not self._selected_id:
            self._mostrar_aviso("Selecciona un estudiante primero.")
            return
        self._app.abrir_perfil(self._selected_id)

    def _on_save(self) -> None:
        self.refresh()

    def _mostrar_aviso(self, msg: str) -> None:
        dlg = ctk.CTkToplevel(self)
        dlg.title("Aviso")
        dlg.geometry("300x120")
        dlg.grab_set()
        ctk.CTkLabel(dlg, text=msg, font=FONTS["body"]).pack(pady=24)
        ActionButton(dlg, "OK", command=dlg.destroy).pack()


class FormularioEstudiante(ctk.CTkToplevel):
    """Formulario para crear o editar un estudiante."""

    def __init__(self, master, estudiante: Optional[Estudiante] = None, on_save=None) -> None:
        super().__init__(master)
        self.withdraw()
        self._estudiante = estudiante
        self._on_save = on_save
        self._is_edit = estudiante is not None

        self.title("Editar Estudiante" if self._is_edit else "Nuevo Estudiante")
        self.geometry("680x620")
        self.grab_set()
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_main"])

        self._fields: dict = {}
        self._build()
        self.update_idletasks()
        self.deiconify()
        self.lift()

    def _build(self) -> None:
        # Header
        hdr = ctk.CTkFrame(self, fg_color=COLORS["primary"], corner_radius=0, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        title = "Editar Estudiante" if self._is_edit else "Registrar Nuevo Estudiante"
        ctk.CTkLabel(hdr, text=title, font=FONTS["heading_md"],
                     text_color="white").pack(side="left", padx=20, pady=14)

        # Scroll
        scroll = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_main"])
        scroll.pack(fill="both", expand=True, padx=20, pady=16)

        # Grid de campos
        campos = [
            ("Código", "codigo", False),
            ("Nombre *", "nombre", False),
            ("Apellido *", "apellido", False),
            ("Correo", "correo", False),
            ("Teléfono", "telefono", False),
            ("Ciclo", "ciclo", False),
            ("Fecha Ingreso (YYYY-MM-DD)", "fecha_ingreso", False),
            ("Monitor", "monitor", False),
        ]

        for i, (label, field, _) in enumerate(campos):
            row, col = divmod(i, 2)
            frame = ctk.CTkFrame(scroll, fg_color="transparent")
            frame.grid(row=row, column=col, padx=10, pady=6, sticky="ew")
            scroll.grid_columnconfigure(0, weight=1)
            scroll.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(frame, text=label, font=FONTS["body_sm"],
                         text_color=COLORS["text_secondary"]).pack(anchor="w")
            entry = ctk.CTkEntry(frame, height=38, font=FONTS["body"],
                                 border_color=COLORS["border"], corner_radius=8)
            entry.pack(fill="x")
            self._fields[field] = entry

        # Selects
        row_sel = (len(campos) + 1) // 2
        for i, (label, field, options) in enumerate([
            ("Universidad", "universidad", UNIVERSIDADES),
            ("Carrera", "carrera", CARRERAS),
            ("Estado", "estado", ESTADOS_ESTUDIANTE),
        ]):
            frame = ctk.CTkFrame(scroll, fg_color="transparent")
            frame.grid(row=row_sel + i // 2, column=i % 2, padx=10, pady=6, sticky="ew")
            ctk.CTkLabel(frame, text=label, font=FONTS["body_sm"],
                         text_color=COLORS["text_secondary"]).pack(anchor="w")
            combo = ctk.CTkComboBox(frame, values=options, height=38, font=FONTS["body"])
            combo.pack(fill="x")
            self._fields[field] = combo

        # Pre-rellenar si es edición
        if self._is_edit and self._estudiante:
            e = self._estudiante
            mapping = {
                "codigo": e.codigo, "nombre": e.nombre, "apellido": e.apellido,
                "correo": e.correo, "telefono": e.telefono, "ciclo": e.ciclo,
                "fecha_ingreso": e.fecha_ingreso, "monitor": e.monitor,
                "universidad": e.universidad, "carrera": e.carrera, "estado": e.estado,
            }
            for field, value in mapping.items():
                widget = self._fields.get(field)
                if widget and value:
                    if isinstance(widget, ctk.CTkEntry):
                        widget.insert(0, str(value))
                    elif isinstance(widget, ctk.CTkComboBox):
                        widget.set(str(value))

        # Error label
        self._error_lbl = ctk.CTkLabel(scroll, text="", font=FONTS["body_sm"],
                                        text_color=COLORS["danger"])
        self._error_lbl.grid(row=row_sel + 3, column=0, columnspan=2, padx=10)

        # Botones
        btn_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"],
                                 border_width=1, border_color=COLORS["border"],
                                 corner_radius=0, height=60)
        btn_frame.pack(fill="x", side="bottom")
        btn_frame.pack_propagate(False)
        ActionButton(btn_frame, "💾 Guardar", command=self._guardar).pack(side="right", padx=16, pady=12)
        ActionButton(btn_frame, "Cancelar", style="secondary", command=self.destroy).pack(side="right", padx=4, pady=12)

    def _get(self, field: str) -> str:
        w = self._fields.get(field)
        if not w:
            return ""
        if isinstance(w, ctk.CTkEntry):
            return w.get().strip()
        elif isinstance(w, ctk.CTkComboBox):
            return w.get().strip()
        return ""

    def _guardar(self) -> None:
        try:
            svc = self.master._app.services["estudiantes"]
            datos = Estudiante(
                id=self._estudiante.id if self._is_edit else None,
                codigo=self._get("codigo"),
                nombre=self._get("nombre"),
                apellido=self._get("apellido"),
                universidad=self._get("universidad"),
                carrera=self._get("carrera"),
                ciclo=self._get("ciclo"),
                correo=self._get("correo"),
                telefono=self._get("telefono"),
                fecha_ingreso=self._get("fecha_ingreso"),
                monitor=self._get("monitor"),
                estado=self._get("estado") or "Activo",
            )
            if self._is_edit:
                svc.actualizar(datos)
            else:
                svc.crear(datos)
            if self._on_save:
                self._on_save()
            self.destroy()
        except ValueError as exc:
            self._error_lbl.configure(text=str(exc))
        except Exception as exc:
            self._error_lbl.configure(text=str(exc))
