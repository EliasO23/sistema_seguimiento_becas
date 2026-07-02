"""Vista de gestión de rendimiento académico."""

from __future__ import annotations

import threading
from datetime import datetime
from typing import TYPE_CHECKING, Optional

import customtkinter as ctk
import pandas as pd

from config import COLORS, FONTS
from services.rendimiento import Rendimiento
from ui.components.cards import ActionButton, DataTable, KPICard, SearchBar, AutocompleteEntry

if TYPE_CHECKING:
    from ui.app import App


class RendimientoView(ctk.CTkFrame):
    """Pantalla de listado y CRUD de rendimiento académico."""

    COLUMNS = ["ID", "Estudiante", "Promedio", "Aprobadas", "Reprobadas", "En Riesgo", "Actualizado"]

    def __init__(self, master, app: "App", **kwargs) -> None:
        super().__init__(master, fg_color=COLORS["bg_main"], **kwargs)
        self._app = app
        self._selected_id: Optional[int] = None
        self._all_rows: list[list[str]] = []
        self._build()

    def _build(self) -> None:
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], height=64, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header,
            text="Rendimiento Académico",
            font=FONTS["heading_lg"],
            text_color=COLORS["text_primary"],
        ).pack(side="left", padx=24, pady=16)

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right", padx=24, pady=12)
        ActionButton(btn_frame, "➕ Nuevo Registro", command=self._abrir_formulario).pack(side="left", padx=4)
        ActionButton(btn_frame, "✏️ Editar", style="secondary", command=self._editar_seleccionado).pack(side="left", padx=4)
        ActionButton(btn_frame, "🗑 Eliminar", style="danger", command=self._eliminar_seleccionado).pack(side="left", padx=4)

        content = ctk.CTkFrame(self, fg_color=COLORS["bg_main"])
        content.pack(fill="both", expand=True, padx=20, pady=16)

        stats = ctk.CTkFrame(content, fg_color="transparent")
        stats.pack(fill="x", pady=(0, 14))
        stats.grid_columnconfigure(0, weight=1)
        stats.grid_columnconfigure(1, weight=1)
        stats.grid_columnconfigure(2, weight=1)

        self._avg_card = KPICard(
            stats,
            "Nota promedio global",
            "0.00",
            subtitle="Promedio general de la hoja",
            icon="📈",
            accent_color=COLORS["primary"],
        )
        self._avg_card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        self._fail_card = KPICard(
            stats,
            "Estudiantes con reprobadas",
            "0",
            subtitle="Último registro por estudiante",
            icon="⚠️",
            accent_color=COLORS["danger"],
        )
        self._fail_card.grid(row=0, column=1, padx=8, sticky="nsew")

        self._total_card = KPICard(
            stats,
            "Registros cargados",
            "0",
            subtitle="Entradas totales de rendimiento",
            icon="🧾",
            accent_color=COLORS["success"],
        )
        self._total_card.grid(row=0, column=2, padx=(8, 0), sticky="nsew")

        filter_bar = ctk.CTkFrame(content, fg_color="transparent")
        filter_bar.pack(fill="x", pady=(0, 12))

        self._search = SearchBar(filter_bar, placeholder="Buscar por estudiante, promedio o fecha...", command=self._on_search)
        self._search.pack(side="left", fill="x", expand=True)

        table_frame = ctk.CTkFrame(
            content,
            fg_color=COLORS["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        table_frame.pack(fill="both", expand=True)
        self._table = DataTable(table_frame, columns=self.COLUMNS, height=440)
        self._table.pack(fill="both", expand=True, padx=4, pady=4)

        self._status = ctk.CTkLabel(content, text="", font=FONTS["caption"], text_color=COLORS["text_secondary"])
        self._status.pack(anchor="w", pady=(8, 0))

        self.refresh()

    def refresh(self) -> None:
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self) -> None:
        try:
            excel = self._app.services["excel"]
            svc_est = self._app.services["estudiantes"]
            df = excel.read_sheet("Rendimiento")
            est_map = {str(e.id): e.nombre_completo for e in svc_est.listar_todos()}

            rows: list[list[str]] = []
            if not df.empty:
                for _, row in df.iterrows():
                    eid = str(row.get("IDEstudiante", "") or "")
                    promedio = self._safe_float(row.get("Promedio"))
                    aprobadas = self._safe_int(row.get("MateriasAprobadas"))
                    reprobadas = self._safe_int(row.get("MateriasReprobadas"))
                    en_riesgo = self._safe_int(row.get("MateriasEnRiesgo"))
                    rows.append([
                        str(row.get("ID", "") or ""),
                        est_map.get(eid, f"ID:{eid}"),
                        f"{promedio:.2f}",
                        str(aprobadas),
                        str(reprobadas),
                        str(en_riesgo),
                        str(row.get("FechaActualizacion", "") or "")[:10],
                    ])

            promedio_global = self._calc_promedio_global(df)
            estudiantes_reprobadas = self._calc_estudiantes_reprobadas(df)

            self._all_rows = rows
            self.after(0, lambda: self._render(rows, promedio_global, estudiantes_reprobadas))
        except Exception as exc:
            self.after(0, lambda exc=exc: self._status.configure(text=f"Error: {exc}", text_color=COLORS["danger"]))

    def _render(self, rows: list[list[str]], promedio_global: float, estudiantes_reprobadas: int) -> None:
        self._table.load_data(rows, on_select=self._on_select)
        shown = self._table.rendered_rows
        total = len(rows)
        extra = f" — mostrando {shown} por rendimiento" if shown < total else ""
        self._status.configure(text=f"{total} registro(s){extra}", text_color=COLORS["text_secondary"])

        color_prom = COLORS["success"] if promedio_global >= 7 else COLORS["warning"]
        self._avg_card.update_value(f"{promedio_global:.2f}")
        self._avg_card.configure(border_color=color_prom)
        self._fail_card.update_value(str(estudiantes_reprobadas))
        self._total_card.update_value(str(total))

    def _on_select(self, row_idx: int, row_data: list[str]) -> None:
        try:
            self._selected_id = int(row_data[0])
        except (ValueError, IndexError):
            self._selected_id = None

    def _on_search(self, query: str) -> None:
        if not query:
            self._table.load_data(self._all_rows, on_select=self._on_select)
            return
        q = query.lower()
        filtered = [r for r in self._all_rows if any(q in str(c).lower() for c in r)]
        self._table.load_data(filtered, on_select=self._on_select)

    def _abrir_formulario(self, rendimiento: Optional[Rendimiento] = None) -> None:
        FormularioRendimiento(self, rendimiento=rendimiento, on_save=self.refresh)

    def _editar_seleccionado(self) -> None:
        if not self._selected_id:
            return
        rendimiento = self._app.services["rendimiento"].obtener_por_id(self._selected_id)
        if rendimiento:
            self._abrir_formulario(rendimiento)

    def _eliminar_seleccionado(self) -> None:
        if not self._selected_id:
            return
        dialogo = ctk.CTkToplevel(self)
        dialogo.title("Confirmar eliminación")
        dialogo.geometry("380x160")
        dialogo.grab_set()
        dialogo.protocol("WM_DELETE_WINDOW", dialogo.destroy)

        ctk.CTkLabel(
            dialogo,
            text="¿Eliminar este registro de rendimiento?\nEsta acción no se puede deshacer.",
            font=FONTS["body"],
            text_color=COLORS["text_primary"],
        ).pack(pady=24)
        btn_frame = ctk.CTkFrame(dialogo, fg_color="transparent")
        btn_frame.pack()

        def confirmar() -> None:
            self._app.services["rendimiento"].eliminar(self._selected_id)
            self._selected_id = None
            dialogo.destroy()
            self.refresh()

        ActionButton(btn_frame, "Eliminar", style="danger", command=confirmar).pack(side="left", padx=8)
        ActionButton(btn_frame, "Cancelar", style="secondary", command=dialogo.destroy).pack(side="left", padx=8)

    @staticmethod
    def _safe_float(value) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _safe_int(value) -> int:
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return 0

    def _calc_promedio_global(self, df: pd.DataFrame) -> float:
        if df.empty or "Promedio" not in df.columns:
            return 0.0
        promedios = pd.to_numeric(df["Promedio"], errors="coerce").dropna()
        return round(float(promedios.mean()), 2) if not promedios.empty else 0.0

    def _calc_estudiantes_reprobadas(self, df: pd.DataFrame) -> int:
        if df.empty or "IDEstudiante" not in df.columns or "MateriasReprobadas" not in df.columns:
            return 0
        data = df.copy()
        data["FechaActualizacion"] = pd.to_datetime(data.get("FechaActualizacion"), errors="coerce")
        data["MateriasReprobadas"] = pd.to_numeric(data["MateriasReprobadas"], errors="coerce").fillna(0)
        data = data.sort_values(["IDEstudiante", "FechaActualizacion"], ascending=[True, True])
        ultimo = data.groupby("IDEstudiante", as_index=False).tail(1)
        return int((ultimo["MateriasReprobadas"] > 0).sum())


class FormularioRendimiento(ctk.CTkToplevel):
    """Formulario para crear o editar rendimiento académico."""

    def __init__(self, master, rendimiento: Optional[Rendimiento] = None, on_save=None) -> None:
        super().__init__(master)
        self.withdraw()
        self._rendimiento = rendimiento
        self._on_save = on_save
        self._is_edit = rendimiento is not None
        self._fields: dict[str, object] = {}

        self.title("Editar Rendimiento" if self._is_edit else "Nuevo Registro de Rendimiento")
        self.geometry("560x470")
        self.grab_set()
        self.configure(fg_color=COLORS["bg_main"])

        self._build()
        self.update_idletasks()
        self.deiconify()
        self.lift()

    def _build(self) -> None:
        hdr = ctk.CTkFrame(self, fg_color=COLORS["primary"], corner_radius=0, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        title = "✏️ Editar Rendimiento" if self._is_edit else "📘 Registrar Rendimiento"
        ctk.CTkLabel(hdr, text=title, font=FONTS["heading_md"], text_color="white").pack(side="left", padx=20, pady=14)

        scroll = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_main"])
        scroll.pack(fill="both", expand=True, padx=20, pady=16)

        estudiantes = self.master._app.services["estudiantes"].listar_todos()
        est_opts = [f"{e.id} - {e.nombre_completo}" for e in estudiantes]

        def lbl(text: str) -> None:
            ctk.CTkLabel(scroll, text=text, font=FONTS["body_sm"], text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(8, 2))

        lbl("Estudiante *")
        self._fields["estudiante"] = AutocompleteEntry(
            scroll,
            values=est_opts,
            height=38,
            font=FONTS["body"],
            placeholder_text="Escribe el nombre o ID del estudiante",
        )
        self._fields["estudiante"].pack(fill="x")

        lbl("Promedio *")
        self._fields["promedio"] = ctk.CTkEntry(scroll, height=38, font=FONTS["body"])
        self._fields["promedio"].pack(fill="x")

        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x", pady=(4, 0))
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

        left = ctk.CTkFrame(grid, fg_color="transparent")
        left.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        def lbl_left(text: str) -> None:
            ctk.CTkLabel(left, text=text, font=FONTS["body_sm"], text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(8, 2))

        lbl_left("Materias aprobadas")
        self._fields["aprobadas"] = ctk.CTkEntry(left, height=38, font=FONTS["body"])
        self._fields["aprobadas"].pack(fill="x")

        lbl_left("Materias reprobadas")
        self._fields["reprobadas"] = ctk.CTkEntry(left, height=38, font=FONTS["body"])
        self._fields["reprobadas"].pack(fill="x")

        right = ctk.CTkFrame(grid, fg_color="transparent")
        right.grid(row=0, column=1, padx=(8, 0), sticky="ew")

        def lbl_right(text: str) -> None:
            ctk.CTkLabel(right, text=text, font=FONTS["body_sm"], text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(8, 2))

        lbl_right("Materias en riesgo")
        self._fields["riesgo"] = ctk.CTkEntry(right, height=38, font=FONTS["body"])
        self._fields["riesgo"].pack(fill="x")

        lbl_right("Fecha actualización (YYYY-MM-DD)")
        self._fields["fecha"] = ctk.CTkEntry(right, height=38, font=FONTS["body"])
        self._fields["fecha"].pack(fill="x")

        self._error = ctk.CTkLabel(scroll, text="", font=FONTS["body_sm"], text_color=COLORS["danger"])
        self._error.pack(pady=(8, 0))

        btn_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], border_width=1, border_color=COLORS["border"], corner_radius=0, height=60)
        btn_frame.pack(fill="x", side="bottom")
        btn_frame.pack_propagate(False)
        ActionButton(btn_frame, "💾 Guardar", command=self._guardar).pack(side="right", padx=16, pady=12)
        ActionButton(btn_frame, "Cancelar", style="secondary", command=self.destroy).pack(side="right", padx=4, pady=12)

        if self._is_edit and self._rendimiento:
            self._cargar_datos()
        else:
            self._fields["fecha"].insert(0, datetime.now().strftime("%Y-%m-%d"))

    def _cargar_datos(self) -> None:
        rendimiento = self._rendimiento
        if not rendimiento:
            return
        estudiantes = self.master._app.services["estudiantes"].listar_todos()
        for opt in [f"{e.id} - {e.nombre_completo}" for e in estudiantes]:
            if opt.startswith(f"{rendimiento.id_estudiante} -"):
                self._fields["estudiante"].set(opt)
                break
        self._fields["promedio"].insert(0, str(rendimiento.promedio))
        self._fields["aprobadas"].insert(0, str(rendimiento.materias_aprobadas))
        self._fields["reprobadas"].insert(0, str(rendimiento.materias_reprobadas))
        self._fields["riesgo"].insert(0, str(rendimiento.materias_en_riesgo))
        self._fields["fecha"].insert(0, rendimiento.fecha_actualizacion)

    def _get(self, field: str) -> str:
        widget = self._fields.get(field)
        if isinstance(widget, ctk.CTkEntry):
            return widget.get().strip()
        if isinstance(widget, ctk.CTkComboBox):
            return widget.get().strip()
        if hasattr(widget, "get_selected_value"):
            return widget.get_selected_value().strip()
        if hasattr(widget, "get"):
            return widget.get().strip()
        return ""

    def _guardar(self) -> None:
        try:
            estudiante_valor = self._get("estudiante")
            if not estudiante_valor:
                raise ValueError("Selecciona un estudiante.")
            estudiante_id = int(estudiante_valor.split(" - ", 1)[0])

            promedio = float(self._get("promedio"))
            aprobadas = int(self._get("aprobadas") or 0)
            reprobadas = int(self._get("reprobadas") or 0)
            riesgo = int(self._get("riesgo") or 0)
            fecha = self._get("fecha") or datetime.now().strftime("%Y-%m-%d")

            if not 0 <= promedio <= 10:
                raise ValueError("El promedio debe estar entre 0 y 10.")
            if aprobadas < 0 or reprobadas < 0 or riesgo < 0:
                raise ValueError("Las cantidades de materias no pueden ser negativas.")
            if not fecha:
                raise ValueError("La fecha de actualización es obligatoria.")

            svc = self.master._app.services["rendimiento"]
            data = Rendimiento(
                id=self._rendimiento.id if self._is_edit and self._rendimiento else None,
                id_estudiante=estudiante_id,
                promedio=promedio,
                materias_aprobadas=aprobadas,
                materias_reprobadas=reprobadas,
                materias_en_riesgo=riesgo,
                fecha_actualizacion=fecha,
            )

            if self._is_edit and data.id:
                svc.actualizar(data)
            else:
                svc.registrar(data)

            if self._on_save:
                self._on_save()
            self.destroy()
        except Exception as exc:
            self._error.configure(text=str(exc))