"""Vista de registro de asistencia."""

from __future__ import annotations

import threading
from datetime import datetime
from typing import TYPE_CHECKING, Optional

import customtkinter as ctk

from config import COLORS, FONTS, ESTADOS_ASISTENCIA
from services.asistencia import Asistencia
from ui.components.cards import SectionHeader, SearchBar, ActionButton, DataTable, AutocompleteEntry

if TYPE_CHECKING:
    from ui.app import App


class AsistenciaView(ctk.CTkFrame):
    """Vista de gestión de asistencias."""

    COLUMNS = ["ID", "Estudiante", "Presente", "Ausente", "Tardanza", "Justificado", "Asistencia"]

    def __init__(self, master, app: "App", **kwargs) -> None:
        super().__init__(master, fg_color=COLORS["bg_main"], **kwargs)
        self._app = app
        self._selected_id: Optional[int] = None
        self._all_rows: list = []
        self._active_query = ""
        self._active_estado = "Todos"
        self._active_mes = "Todos"
        self._build()

    def _build(self) -> None:
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], height=64, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="Control de Asistencia",
                     font=FONTS["heading_lg"],
                     text_color=COLORS["text_primary"]).pack(side="left", padx=24, pady=16)

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right", padx=24, pady=12)
        ActionButton(btn_frame, "➕ Registrar", command=self._abrir_form).pack(side="left", padx=4)

        # Panel superior con stats
        top = ctk.CTkFrame(self, fg_color=COLORS["bg_main"])
        top.pack(fill="x", padx=20, pady=(16, 0))

        self._stats_frame = ctk.CTkFrame(top, fg_color=COLORS["bg_card"],
                                          corner_radius=12, border_width=1,
                                          border_color=COLORS["border"])
        self._stats_frame.pack(fill="x", pady=(0, 12))
        self._stats_lbl = ctk.CTkLabel(self._stats_frame,
                                        text="Asistencia promedio global: Calculando...",
                                        font=FONTS["heading_md"],
                                        text_color=COLORS["text_primary"])
        self._stats_lbl.pack(padx=16, pady=12)

        content = ctk.CTkFrame(self, fg_color=COLORS["bg_main"])
        content.pack(fill="both", expand=True, padx=20, pady=4)

        # Filtros
        filter_bar = ctk.CTkFrame(content, fg_color="transparent")
        filter_bar.pack(fill="x", pady=(0, 12))

        self._search = SearchBar(filter_bar, placeholder="Buscar por estudiante, fecha...",
                                  command=self._on_search)
        self._search.pack(side="left", fill="x", expand=True, padx=(0, 12))

        ctk.CTkLabel(filter_bar, text="Mes:", font=FONTS["body_sm"],
                     text_color=COLORS["text_secondary"]).pack(side="left", padx=(0, 4))
        self._filtro_mes = ctk.CTkComboBox(
            filter_bar,
            values=["Todos"],
            width=140, height=36,
            font=FONTS["body_sm"],
            command=self._on_filtro_mes,
        )
        self._filtro_mes.set("Todos")
        self._filtro_mes.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(filter_bar, text="Estado:", font=FONTS["body_sm"],
                     text_color=COLORS["text_secondary"]).pack(side="left", padx=(0, 4))
        self._filtro = ctk.CTkComboBox(
            filter_bar,
            values=["Todos"] + ESTADOS_ASISTENCIA,
            width=140, height=36,
            font=FONTS["body_sm"],
            command=self._on_filtro,
        )
        self._filtro.set("Todos")
        self._filtro.pack(side="left")

        # Tabla
        table_frame = ctk.CTkFrame(content, fg_color=COLORS["bg_card"],
                                   corner_radius=12, border_width=1, border_color=COLORS["border"])
        table_frame.pack(fill="both", expand=True)
        self._table = DataTable(table_frame, columns=self.COLUMNS, height=420)
        self._table.pack(fill="both", expand=True, padx=4, pady=4)

        self._status = ctk.CTkLabel(content, text="", font=FONTS["caption"],
                                     text_color=COLORS["text_secondary"])
        self._status.pack(anchor="w", pady=(8, 0))

        self._table.load_data([], on_select=self._on_select)
        self._status.configure(text="Cargando asistencia...", text_color=COLORS["text_secondary"])
        self.refresh()

    def refresh(self) -> None:
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self) -> None:
        try:
            svc_asi = self._app.services["asistencia"]
            svc_est = self._app.services["estudiantes"]
            df = self._app.services["excel"].read_sheet("Asistencias")
            est_map = {str(e.id): e.nombre_completo for e in svc_est.listar_todos()}
            pct_global = svc_asi.promedio_asistencia_global()

            meses = svc_asi.meses_disponibles(df)
            if self._filtro_mes.winfo_exists():
                self._filtro_mes.configure(values=["Todos"] + meses)
                if self._active_mes not in (["Todos"] + meses):
                    self._active_mes = "Todos"
                    self._filtro_mes.set("Todos")

            resumen = svc_asi.resumen_por_estudiante(df, mes=self._active_mes if self._active_mes != "Todos" else None)
            rows = []
            for item in resumen:
                eid = item["id"]
                rows.append([
                    eid,
                    est_map.get(eid, f"ID:{eid}"),
                    str(item["presentes"]),
                    str(item["ausentes"]),
                    str(item["tardanzas"]),
                    str(item["justificados"]),
                    f"{item['pct_asistencia']:.1f}%",
                ])
            self._all_rows = rows

            self.after(0, lambda: self._render(rows, len(rows), pct_global))
        except Exception as exc:
            self.after(0, lambda exc=exc: self._status.configure(
                text=f"Error: {exc}", text_color=COLORS["danger"]))

    def _render(self, rows, total, pct_global) -> None:
        self._all_rows = rows
        if self._active_mes == "Todos" and self._active_estado == "Todos" and not self._active_query:
            self._table.load_data(rows, on_select=self._on_select)
        else:
            self._aplicar_filtros()

        shown = self._table.rendered_rows
        extra = f" — mostrando {shown} por rendimiento" if shown < total else ""
        self._status.configure(
            text=f"{shown} estudiante(s){extra}",
            text_color=COLORS["text_secondary"],
        )

        color = COLORS["success"] if pct_global >= 75 else COLORS["danger"]
        self._stats_lbl.configure(
            text=f"📊  Asistencia promedio global: {pct_global:.1f}%  —  "
                 f"{'✅ Por encima del mínimo' if pct_global >= 75 else '⚠️ Por debajo del 75% requerido'}",
            text_color=color,
        )

    def _on_select(self, row_idx, row_data) -> None:
        try:
            from ui.perfil import PerfilEstudianteView
            estudiante_id = int(row_data[0])
            PerfilEstudianteView(self._app, estudiante_id)
        except (ValueError, IndexError):
            pass

    def _aplicar_filtros(self) -> None:
        rows = list(self._all_rows)
        if self._active_estado != "Todos":
            idx = {"Presente": 2, "Ausente": 3, "Tardanza": 4, "Justificado": 5}[self._active_estado]
            rows = [r for r in rows if int(r[idx]) > 0]
        if self._active_query:
            q = self._active_query.lower()
            rows = [r for r in rows if any(q in str(c).lower() for c in r)]
        self._table.load_data(rows, on_select=self._on_select)

    def _on_search(self, query: str) -> None:
        self._active_query = query or ""
        self._aplicar_filtros()

    def _on_filtro(self, estado: str) -> None:
        self._active_estado = estado
        self._aplicar_filtros()

    def _on_filtro_mes(self, mes: str) -> None:
        self._active_mes = mes
        self.refresh()

    def _abrir_form(self) -> None:
        FormularioAsistencia(self, on_save=self.refresh)

    def _eliminar(self) -> None:
        if not self._selected_id:
            self._mostrar_aviso("Selecciona un estudiante primero.")
            return
        self._mostrar_aviso("La eliminación se gestiona desde el registro detallado del estudiante.")

    def _mostrar_aviso(self, msg: str) -> None:
        dlg = ctk.CTkToplevel(self)
        dlg.title("Aviso")
        dlg.geometry("300x120")
        dlg.grab_set()
        ctk.CTkLabel(dlg, text=msg, font=FONTS["body"]).pack(pady=24)
        ActionButton(dlg, "OK", command=dlg.destroy).pack()


class FormularioAsistencia(ctk.CTkToplevel):
    """Formulario para registrar asistencia."""

    def __init__(self, master, on_save=None, estudiante_id: Optional[int] = None) -> None:
        super().__init__(master)
        self.withdraw()
        self._on_save = on_save
        self._preset_id = estudiante_id
        self.title("Registrar Asistencia")
        self.geometry("480x550")
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
        ctk.CTkLabel(hdr, text="✅ Registrar Asistencia", font=FONTS["heading_md"],
                     text_color="white").pack(side="left", padx=20, pady=14)

        form = ctk.CTkFrame(self, fg_color=COLORS["bg_main"])
        form.pack(fill="both", expand=True, padx=24, pady=16)

        try:
            app = self.master._app
        except AttributeError:
            app = self.master.master._app

        estudiantes = app.services["estudiantes"].listar_activos()
        est_opts = [f"{e.id} - {e.nombre_completo}" for e in estudiantes]

        def lbl(text):
            ctk.CTkLabel(form, text=text, font=FONTS["body_sm"],
                         text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(10, 2))

        lbl("Estudiante *")
        self._est = AutocompleteEntry(
            form,
            values=est_opts,
            height=38,
            font=FONTS["body"],
            placeholder_text="Escribe el nombre o ID del estudiante",
        )
        self._est.pack(fill="x")
        if self._preset_id:
            for opt in est_opts:
                if opt.startswith(f"{self._preset_id} -"):
                    self._est.set(opt)
                    break

        lbl("Fecha *")
        self._fecha = ctk.CTkEntry(form, height=38, font=FONTS["body"])
        self._fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self._fecha.pack(fill="x")

        lbl("Estado *")
        self._estado = ctk.CTkComboBox(form, values=ESTADOS_ASISTENCIA, height=38, font=FONTS["body"])
        self._estado.set("Presente")
        self._estado.pack(fill="x")

        lbl("Observación")
        self._obs = ctk.CTkEntry(form, height=38, font=FONTS["body"])
        self._obs.pack(fill="x")

        self._error = ctk.CTkLabel(form, text="", font=FONTS["body_sm"],
                                    text_color=COLORS["danger"])
        self._error.pack(pady=6)

        btn_f = ctk.CTkFrame(self, fg_color=COLORS["bg_card"],
                              border_width=1, border_color=COLORS["border"],
                              corner_radius=0, height=60)
        btn_f.pack(fill="x", side="bottom")
        btn_f.pack_propagate(False)
        ActionButton(btn_f, "💾 Guardar", command=self._guardar).pack(side="right", padx=16, pady=12)
        ActionButton(btn_f, "Cancelar", style="secondary", command=self.destroy).pack(side="right", padx=4, pady=12)

    def _guardar(self) -> None:
        try:
            est_sel = self._est.get_selected_value()
            if not est_sel:
                raise ValueError("Selecciona un estudiante.")
            eid = int(est_sel.split(" - ", 1)[0])
            try:
                app = self.master._app
            except AttributeError:
                app = self.master.master._app
            asi = Asistencia(
                id_estudiante=eid,
                fecha=self._fecha.get().strip(),
                estado=self._estado.get(),
                observacion=self._obs.get().strip(),
            )
            app.services["asistencia"].registrar(asi)
            if self._on_save:
                self._on_save()
            self.destroy()
        except ValueError as exc:
            self._error.configure(text=str(exc))
        except Exception as exc:
            self._error.configure(text=str(exc))
