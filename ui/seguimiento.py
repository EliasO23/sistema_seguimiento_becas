"""Vista de seguimiento y registro de conversaciones."""

from __future__ import annotations

import sys
import threading
from datetime import datetime
from typing import TYPE_CHECKING, Optional

import customtkinter as ctk

from config import COLORS, FONTS, TIPOS_SEGUIMIENTO
from services.seguimiento import Seguimiento
from ui.components.cards import SectionHeader, SearchBar, ActionButton, DataTable, AutocompleteEntry

if TYPE_CHECKING:
    from ui.app import App


class SeguimientoView(ctk.CTkFrame):
    """Vista de seguimientos con lista y formulario."""

    COLUMNS = ["ID", "Estudiante", "Fecha", "Tipo", "Descripción", "Próximo Seg."]

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
        ctk.CTkLabel(header, text="Registro de Seguimientos",
                     font=FONTS["heading_lg"],
                     text_color=COLORS["text_primary"]).pack(side="left", padx=24, pady=16)

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right", padx=24, pady=12)
        ActionButton(btn_frame, "➕ Nuevo Seguimiento", command=self._abrir_form).pack(side="left", padx=4)
        ActionButton(btn_frame, "🗑 Eliminar", style="danger",
                     command=self._eliminar).pack(side="left", padx=4)

        content = ctk.CTkFrame(self, fg_color=COLORS["bg_main"])
        content.pack(fill="both", expand=True, padx=20, pady=16)

        # Próximos seguimientos
        prox_frame = ctk.CTkFrame(content, fg_color=COLORS["bg_card"],
                                  corner_radius=12, border_width=1, border_color=COLORS["border"])
        prox_frame.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(prox_frame, text="📅 Próximos Seguimientos (próximos 7 días)",
                     font=FONTS["heading_md"], text_color=COLORS["primary"]).pack(anchor="w", padx=16, pady=(12, 4))
        self._prox_lbl = ctk.CTkLabel(prox_frame, text="Cargando...",
                                       font=FONTS["body"],
                                       text_color=COLORS["text_secondary"],
                                       justify="left",
                                       anchor="w",)
        self._prox_lbl.pack(fill="x", padx=20, pady=(0, 12))

        # Búsqueda
        self._search = SearchBar(content, placeholder="Buscar seguimiento...",
                                  command=self._on_search)
        self._search.pack(fill="x", pady=(0, 12))

        # Tabla
        table_frame = ctk.CTkFrame(content, fg_color=COLORS["bg_card"],
                                   corner_radius=12, border_width=1, border_color=COLORS["border"])
        table_frame.pack(fill="both", expand=True)
        self._table = DataTable(table_frame, columns=self.COLUMNS, height=400)
        self._table.pack(fill="both", expand=True, padx=4, pady=4)

        self._status = ctk.CTkLabel(content, text="", font=FONTS["caption"],
                                     text_color=COLORS["text_secondary"])
        self._status.pack(anchor="w", pady=(8, 0))

        self.refresh()

    def refresh(self) -> None:
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self) -> None:
        try:
            svc_seg = self._app.services["seguimiento"]
            svc_est = self._app.services["estudiantes"]
            df = self._app.services["excel"].read_sheet("Seguimientos")
            est_map = {str(e.id): e.nombre_completo for e in svc_est.listar_todos()}

            rows = []
            for _, row in df.iterrows():
                eid = str(row.get("IDEstudiante", ""))
                rows.append([
                    str(row.get("ID", "")),
                    est_map.get(eid, f"ID:{eid}"),
                    str(row.get("Fecha", ""))[:10],
                    str(row.get("Tipo", "")),
                    str(row.get("Descripcion", ""))[:40],
                    str(row.get("ProximoSeguimiento", ""))[:10],
                ])
            self._all_rows = rows

            # Próximos
            proximos = svc_seg.proximos_seguimientos()
            if proximos.empty:
                prox_texto = "No hay seguimientos programados en los próximos 7 días."
            else:
                items = []
                for _, r in proximos.iterrows():
                    eid = str(r.get("IDEstudiante", ""))
                    nombre = est_map.get(eid, f"ID:{eid}")
                    fecha = str(r.get("ProximoSeguimiento", ""))[:10]
                    items.append(f"• {nombre} — {fecha}")
                prox_texto = "\n".join(items[:5])

            self.after(0, lambda: self._render(rows, len(rows), prox_texto))
        except Exception as exc:
            self.after(0, lambda exc=exc: self._status.configure(text=f"Error: {exc}", text_color=COLORS["danger"]))

    def _render(self, rows, total, prox_texto) -> None:
        self._table.load_data(rows, on_select=self._on_select)
        shown = self._table.rendered_rows
        extra = f" — mostrando {shown} por rendimiento" if shown < total else ""
        self._status.configure(text=f"{total} seguimiento(s){extra}", text_color=COLORS["text_secondary"])
        self._prox_lbl.configure(text=prox_texto)

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
        FormularioSeguimiento(self, on_save=self.refresh)

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
            text="¿Eliminar este registro de seguimiento?\nEsta acción no se puede deshacer.",
            font=FONTS["body"],
            text_color=COLORS["text_primary"],
        ).pack(pady=24)
        btn_frame = ctk.CTkFrame(dialogo, fg_color="transparent")
        btn_frame.pack()

        def confirmar() -> None:
            self._app.services["seguimiento"].eliminar(self._selected_id)
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


class FormularioSeguimiento(ctk.CTkToplevel):
    """Formulario de registro de seguimiento."""

    def __init__(self, master, on_save=None, estudiante_id: Optional[int] = None) -> None:
        super().__init__(master)
        self.withdraw()
        self._on_save = on_save
        self._preset_id = estudiante_id
        self.title("Nuevo Seguimiento")
        self.geometry("600x560")
        self.grab_set()
        self.configure(fg_color=COLORS["bg_main"])
        self._estudiantes: list = []
        self._build()
        self.update_idletasks()
        self.deiconify()
        self.lift()

    def _build(self) -> None:
        hdr = ctk.CTkFrame(self, fg_color=COLORS["primary"], corner_radius=0, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="💬 Registrar Seguimiento", font=FONTS["heading_md"],
                     text_color="white").pack(side="left", padx=20, pady=14)

        scroll = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_main"])
        scroll.pack(fill="both", expand=True, padx=20, pady=16)

        # Cargar estudiantes
        try:
            app = self.master._app
        except AttributeError:
            app = self.master.master._app
        self._estudiantes = app.services["estudiantes"].listar_activos()
        est_opts = [f"{e.id} - {e.nombre_completo}" for e in self._estudiantes]

        def lbl(text):
            ctk.CTkLabel(scroll, text=text, font=FONTS["body"],
                         text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(8, 2))

        lbl("Estudiante *")
        self._est_combo = AutocompleteEntry(
            scroll,
            values=est_opts,
            height=38,
            font=FONTS["body"],
            placeholder_text="Escribe el nombre o ID del estudiante",
        )
        self._est_combo.pack(fill="x")
        if self._preset_id:
            for opt in est_opts:
                if opt.startswith(f"{self._preset_id} -"):
                    self._est_combo.set(opt)
                    break

        lbl("Fecha *")
        self._fecha = ctk.CTkEntry(scroll, height=38, font=FONTS["body"], border_color=COLORS["border"])
        self._fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self._fecha.pack(fill="x")

        lbl("Tipo *")
        self._tipo = ctk.CTkComboBox(scroll, values=TIPOS_SEGUIMIENTO, height=38, font=FONTS["body"], 
                                     border_color=COLORS["border"],
                                     button_color=COLORS["primary_light"],
                                     button_hover_color=COLORS["primary"],
                                     dropdown_fg_color="white",
                                     dropdown_hover_color=COLORS["primary_light"],
                                     )
        self._tipo.pack(fill="x")

        lbl("Descripción *")
        self._desc = ctk.CTkTextbox(scroll, height=80, font=FONTS["body"],
                                     border_color=COLORS["border"], border_width=1)
        self._desc.pack(fill="x")

        lbl("Acción realizada")
        self._accion = ctk.CTkTextbox(scroll, height=60, font=FONTS["body"],
                                       border_color=COLORS["border"], border_width=1)
        self._accion.pack(fill="x")

        lbl("Próximo seguimiento")
        self._proximo = ctk.CTkEntry(scroll, height=38, font=FONTS["body"], placeholder_text="AAAA-MM-DD", border_color=COLORS["border"])
        self._proximo.pack(fill="x")

        lbl("Observaciones")
        self._obs = ctk.CTkTextbox(scroll, height=60, font=FONTS["body"],
                                    border_color=COLORS["border"], border_width=1)
        self._obs.pack(fill="x")

        self._redirigir_scroll(scroll, self._desc, self._accion, self._obs)

        self._error_lbl = ctk.CTkLabel(scroll, text="", font=FONTS["body_sm"],
                                        text_color=COLORS["danger"])
        self._error_lbl.pack(pady=4)

        btn_f = ctk.CTkFrame(self, fg_color=COLORS["bg_card"],
                              border_width=1, border_color=COLORS["border"],
                              corner_radius=0, height=60)
        btn_f.pack(fill="x", side="bottom")
        btn_f.pack_propagate(False)
        ActionButton(btn_f, "💾 Guardar", command=self._guardar).pack(side="right", padx=16, pady=12)
        ActionButton(btn_f, "Cancelar", style="secondary", command=self.destroy).pack(side="right", padx=4, pady=12)

    def _redirigir_scroll(self, scroll: ctk.CTkScrollableFrame, *widgets) -> None:
        canvas = getattr(scroll, "_parent_canvas", None)
        if canvas is None:
            return

        def _on_mousewheel(event) -> str:
            if sys.platform.startswith("win"):
                canvas.yview_scroll(-int(event.delta / 6), "units")
            elif sys.platform == "darwin":
                canvas.yview_scroll(-event.delta, "units")
            else:
                canvas.yview_scroll(-1 if event.num == 4 else 1, "units")
            return "break"

        for widget in widgets:
            widget.bind("<MouseWheel>", _on_mousewheel)
            widget.bind("<Button-4>", _on_mousewheel)
            widget.bind("<Button-5>", _on_mousewheel)

    def _guardar(self) -> None:
        try:
            est_sel = self._est_combo.get_selected_value()
            if not est_sel:
                raise ValueError("Selecciona un estudiante.")
            eid = int(est_sel.split(" - ", 1)[0])
            try:
                app = self.master._app
            except AttributeError:
                app = self.master.master._app
            seg = Seguimiento(
                id_estudiante=eid,
                fecha=self._fecha.get().strip(),
                tipo=self._tipo.get(),
                descripcion=self._desc.get("1.0", "end").strip(),
                accion_realizada=self._accion.get("1.0", "end").strip(),
                proximo_seguimiento=self._proximo.get().strip(),
                observaciones=self._obs.get("1.0", "end").strip(),
            )
            app.services["seguimiento"].registrar(seg)
            if self._on_save:
                self._on_save()
            self.destroy()
        except ValueError as exc:
            self._error_lbl.configure(text=str(exc))
