"""Vista de gestión de voluntariado."""

from __future__ import annotations

import threading
from datetime import datetime
from typing import TYPE_CHECKING, Optional

import customtkinter as ctk

from config import COLORS, FONTS
from services.voluntariado import Voluntariado
from ui.components.cards import ActionButton, DataTable, SearchBar

if TYPE_CHECKING:
    from ui.app import App


class VoluntariadoView(ctk.CTkFrame):
    """Vista de voluntariado."""

    COLUMNS = ["ID", "Estudiante", "Actividad", "Horas", "Fecha", "Observación"]

    def __init__(self, master, app: "App", **kwargs) -> None:
        super().__init__(master, fg_color=COLORS["bg_main"], **kwargs)
        self._app = app
        self._selected_id: Optional[int] = None
        self._all_rows: list = []
        self._build()

    def _build(self) -> None:
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], height=64, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="Gestión de Voluntariado",
                     font=FONTS["heading_lg"],
                     text_color=COLORS["text_primary"]).pack(side="left", padx=24, pady=16)
        btn_f = ctk.CTkFrame(header, fg_color="transparent")
        btn_f.pack(side="right", padx=24, pady=12)
        ActionButton(btn_f, "➕ Registrar", command=self._abrir_form).pack(side="left", padx=4)
        ActionButton(btn_f, "🗑 Eliminar", style="danger", command=self._eliminar).pack(side="left", padx=4)

        # Stats globales
        stats_f = ctk.CTkFrame(self, fg_color=COLORS["bg_card"],
                                corner_radius=0, border_width=1, border_color=COLORS["border"])
        stats_f.pack(fill="x", padx=20, pady=(16, 4))
        self._stats_lbl = ctk.CTkLabel(stats_f, text="Calculando...",
                                        font=FONTS["body"], text_color=COLORS["text_primary"])
        self._stats_lbl.pack(padx=16, pady=10)

        content = ctk.CTkFrame(self, fg_color=COLORS["bg_main"])
        content.pack(fill="both", expand=True, padx=20, pady=8)

        self._search = SearchBar(content, placeholder="Buscar voluntariado...",
                                  command=self._on_search)
        self._search.pack(fill="x", pady=(0, 12))

        table_f = ctk.CTkFrame(content, fg_color=COLORS["bg_card"],
                               corner_radius=12, border_width=1, border_color=COLORS["border"])
        table_f.pack(fill="both", expand=True)
        self._table = DataTable(table_f, columns=self.COLUMNS, height=440)
        self._table.pack(fill="both", expand=True, padx=4, pady=4)

        self._status = ctk.CTkLabel(content, text="", font=FONTS["caption"],
                                     text_color=COLORS["text_secondary"])
        self._status.pack(anchor="w", pady=(8, 0))

        self.refresh()

    def refresh(self) -> None:
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self) -> None:
        try:
            svc_vol = self._app.services["voluntariado"]
            svc_est = self._app.services["estudiantes"]
            df = self._app.services["excel"].read_sheet("Voluntariado")
            est_map = {str(e.id): e.nombre_completo for e in svc_est.listar_todos()}
            prom_horas = svc_vol.promedio_horas_global()

            rows = []
            for _, row in df.iterrows():
                eid = str(row.get("IDEstudiante", ""))
                rows.append([
                    str(row.get("ID", "")),
                    est_map.get(eid, f"ID:{eid}"),
                    str(row.get("Actividad", ""))[:35],
                    str(row.get("Horas", "")),
                    str(row.get("Fecha", ""))[:10],
                    str(row.get("Observacion", ""))[:30],
                ])
            self._all_rows = rows
            self.after(0, lambda: self._render(rows, len(rows), prom_horas))
        except Exception as exc:
            self.after(0, lambda: self._status.configure(text=f"Error: {exc}",
                                                          text_color=COLORS["danger"]))

    def _render(self, rows, total, prom_horas) -> None:
        self._table.load_data(rows, on_select=self._on_select)
        shown = self._table.rendered_rows
        extra = f" — mostrando {shown} por rendimiento" if shown < total else ""
        self._status.configure(text=f"{total} registro(s){extra}", text_color=COLORS["text_secondary"])
        self._stats_lbl.configure(
            text=f"🤝  Promedio de horas por estudiante: {prom_horas:.1f}h  "
                 f"(Meta: 40h por estudiante)"
        )

    def _on_select(self, row_idx, row_data) -> None:
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

    def _abrir_form(self) -> None:
        FormularioVoluntariado(self, on_save=self.refresh)

    def _eliminar(self) -> None:
        if not self._selected_id:
            self._mostrar_aviso("Selecciona un registro primero.")
            return
        dialogo = ctk.CTkToplevel(self)
        dialogo.title("Confirmar eliminación")
        dialogo.geometry("360x160")
        dialogo.grab_set()
        dialogo.protocol("WM_DELETE_WINDOW", dialogo.destroy)

        ctk.CTkLabel(
            dialogo,
            text="¿Eliminar este registro de voluntariado?\nEsta acción no se puede deshacer.",
            font=FONTS["body"],
            text_color=COLORS["text_primary"],
        ).pack(pady=24)
        btn_frame = ctk.CTkFrame(dialogo, fg_color="transparent")
        btn_frame.pack()

        def confirmar() -> None:
            self._app.services["voluntariado"].eliminar(self._selected_id)
            self._selected_id = None
            dialogo.destroy()
            self.refresh()

        ActionButton(btn_frame, "Eliminar", style="danger", command=confirmar).pack(side="left", padx=8)
        ActionButton(btn_frame, "Cancelar", style="secondary", command=dialogo.destroy).pack(side="left", padx=8)

    def _mostrar_aviso(self, msg: str) -> None:
        dlg = ctk.CTkToplevel(self)
        dlg.title("Aviso")
        dlg.geometry("300x120")
        dlg.grab_set()
        ctk.CTkLabel(dlg, text=msg, font=FONTS["body"]).pack(pady=24)
        ActionButton(dlg, "OK", command=dlg.destroy).pack()


class FormularioVoluntariado(ctk.CTkToplevel):
    """Formulario para registrar voluntariado."""

    def __init__(self, master, on_save=None, estudiante_id: Optional[int] = None) -> None:
        super().__init__(master)
        self.withdraw()
        self._on_save = on_save
        self._preset_id = estudiante_id
        self.title("Registrar Voluntariado")
        self.geometry("480x420")
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
        ctk.CTkLabel(hdr, text="🤝 Registrar Voluntariado", font=FONTS["heading_md"],
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
        self._est = ctk.CTkComboBox(form, values=est_opts, height=38, font=FONTS["body"])
        self._est.pack(fill="x")
        if self._preset_id:
            for opt in est_opts:
                if opt.startswith(f"{self._preset_id} -"):
                    self._est.set(opt)
                    break

        lbl("Actividad *")
        self._actividad = ctk.CTkEntry(form, height=38, font=FONTS["body"])
        self._actividad.pack(fill="x")

        lbl("Horas realizadas *")
        self._horas = ctk.CTkEntry(form, height=38, font=FONTS["body"])
        self._horas.pack(fill="x")

        lbl("Fecha *")
        self._fecha = ctk.CTkEntry(form, height=38, font=FONTS["body"])
        self._fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self._fecha.pack(fill="x")

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
            est_sel = self._est.get()
            if not est_sel:
                raise ValueError("Selecciona un estudiante.")
            eid = int(est_sel.split(" - ")[0])
            horas_str = self._horas.get().strip()
            if not horas_str:
                raise ValueError("Las horas son obligatorias.")
            horas = float(horas_str)
            try:
                app = self.master._app
            except AttributeError:
                app = self.master.master._app
            vol = Voluntariado(
                id_estudiante=eid,
                actividad=self._actividad.get().strip(),
                horas=horas,
                fecha=self._fecha.get().strip(),
                observacion=self._obs.get().strip(),
            )
            app.services["voluntariado"].registrar(vol)
            if self._on_save:
                self._on_save()
            self.destroy()
        except ValueError as exc:
            self._error.configure(text=str(exc))
        except Exception as exc:
            self._error.configure(text=str(exc))
