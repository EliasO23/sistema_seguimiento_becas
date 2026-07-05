"""Vista de reportes y exportaciones."""

from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import customtkinter as ctk

from config import COLORS, FONTS, EXPORTS_DIR, REPORTS_DIR
from ui.components.cards import ActionButton, SectionHeader, KPICard

if TYPE_CHECKING:
    from ui.app import App


class ReportesView(ctk.CTkFrame):
    """Pantalla de generación de reportes y exportaciones."""

    def __init__(self, master, app: "App", **kwargs) -> None:
        super().__init__(master, fg_color=COLORS["bg_main"], **kwargs)
        self._app = app
        self._build()

    def _build(self) -> None:
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], height=120, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkFrame(header, height=4, fg_color=COLORS["primary"], corner_radius=0).pack(fill="x")
        ctk.CTkLabel(
            header,
            text="Reportes y Exportaciones",
            font=("Segoe UI", 24, "bold"),
            text_color=COLORS["text_primary"],
        ).pack(anchor="w", padx=28, pady=(20, 0))
        ctk.CTkLabel(
            header,
            text="Centraliza la generación de informes, exportaciones y respaldos en un espacio claro y elegante.",
            font=FONTS["body"],
            text_color=COLORS["text_secondary"],
        ).pack(anchor="w", padx=28, pady=(6, 20))

        scroll = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_main"])
        scroll.pack(fill="both", expand=True, padx=24, pady=(18, 24))

        # ── Reportes PDF ──────────────────────────────────────────────────────
        SectionHeader(scroll, "📄 Reportes PDF", "Genera informes profesionales en PDF").pack(
            fill="x", pady=(0, 14))

        pdf_grid = ctk.CTkFrame(scroll, fg_color="transparent")
        pdf_grid.pack(fill="x", pady=(0, 22))
        pdf_grid.grid_columnconfigure(0, weight=1)
        pdf_grid.grid_columnconfigure(1, weight=1)

        self._card_reporte_general(pdf_grid)
        self._card_reporte_riesgo(pdf_grid)

        # ── Exportaciones ─────────────────────────────────────────────────────
        SectionHeader(scroll, "📊 Exportar Datos",
                      "Descarga los datos en diferentes formatos").pack(fill="x", pady=(0, 12))

        exp_grid = ctk.CTkFrame(scroll, fg_color="transparent")
        exp_grid.pack(fill="x", pady=(0, 22))
        exp_grid.grid_columnconfigure(0, weight=1)
        exp_grid.grid_columnconfigure(1, weight=1)
        for i, (icon, titulo, desc, accion) in enumerate([
            ("📗", "Excel Completo", "Descarga todo el archivo de becados en formato Excel.", self._exportar_excel),
            ("📋", "CSV Estudiantes", "Exporta los datos de estudiantes a CSV.", self._exportar_csv_est),
            ("📋", "CSV Asistencias", "Exporta el registro de asistencias a CSV.", self._exportar_csv_asi),
            ("📋", "CSV Seguimientos", "Exporta los seguimientos a CSV.", self._exportar_csv_seg),
        ]):
            row = i // 2
            col = i % 2
            card = ctk.CTkFrame(
                exp_grid,
                fg_color=COLORS["bg_card"],
                corner_radius=18,
                border_width=1,
                border_color=COLORS["border"],
            )
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            exp_grid.grid_rowconfigure(row, weight=1)

            ctk.CTkLabel(card, text=icon, font=("Segoe UI Emoji", 30)).pack(pady=(18, 8))
            ctk.CTkFrame(card, height=2, fg_color=COLORS["primary_light"], corner_radius=0).pack(fill="x", padx=24, pady=(4, 10))
            ctk.CTkLabel(card, text=titulo, font=("Segoe UI", 14, "bold"),
                         text_color=COLORS["text_primary"]).pack()
            ctk.CTkLabel(card, text=desc, font=FONTS["body_sm"],
                         text_color=COLORS["text_secondary"],
                         wraplength=240, justify="center").pack(pady=(6, 14), padx=18)
            ActionButton(card, "Exportar", command=accion).pack(pady=(0, 18))

        # ── Respaldo y registro ────────────────────────────────────────────────
        SectionHeader(scroll, "🛡️ Respaldo y seguimiento",
                      "Gestiona respaldos y revisa la actividad reciente.").pack(fill="x", pady=(0, 12))
        bottom_grid = ctk.CTkFrame(scroll, fg_color="transparent")
        bottom_grid.pack(fill="x", pady=(0, 24))
        bottom_grid.grid_columnconfigure(0, weight=1)
        bottom_grid.grid_columnconfigure(1, weight=1)

        backup_f = ctk.CTkFrame(
            bottom_grid,
            fg_color=COLORS["bg_card"],
            corner_radius=20,
            border_width=1,
            border_color=COLORS["border"],
        )
        backup_f.grid(row=0, column=0, padx=(0, 8), pady=0, sticky="nsew")
        ctk.CTkLabel(
            backup_f,
            text="Crea una copia de seguridad del archivo Excel con fecha y hora.",
            font=FONTS["body"],
            text_color=COLORS["text_secondary"],
            wraplength=420,
            justify="center",
        ).pack(anchor="center", padx=24, pady=(18, 12))
        ActionButton(backup_f, "🔒 Crear Backup Ahora",
                     command=self._crear_backup).pack(anchor="center", padx=20, pady=(0, 18))

        self._log_frame = ctk.CTkFrame(
            bottom_grid,
            fg_color=COLORS["bg_card"],
            corner_radius=18,
            border_width=1,
            border_color=COLORS["border"],
        )
        self._log_frame.grid(row=0, column=1, padx=(8, 0), pady=0, sticky="nsew")
        self._log("Listo para generar reportes.", COLORS["text_secondary"])

    def _card_reporte_general(self, parent) -> None:
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["bg_card"],
            corner_radius=18,
            border_width=1,
            border_color=COLORS["border"],
        )
        card.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="nsew")

        ctk.CTkLabel(card, text="📊", font=("Segoe UI Emoji", 36)).pack(pady=(22, 8))
        ctk.CTkFrame(card, height=2, fg_color=COLORS["primary_light"], corner_radius=0).pack(fill="x", padx=26, pady=(2, 10))
        ctk.CTkLabel(card, text="Reporte General", font=("Segoe UI", 15, "bold"),
                     text_color=COLORS["text_primary"]).pack()
        ctk.CTkLabel(
            card,
            text="Incluye todos los estudiantes, KPIs globales y distribución de riesgos.",
            font=FONTS["body_sm"],
            text_color=COLORS["text_secondary"],
            justify="center",
            wraplength=260,
        ).pack(pady=(8, 16), padx=16)
        ActionButton(card, "📄 Generar PDF General",
                     command=self._generar_reporte_general).pack(pady=(0, 20))

    def _card_reporte_riesgo(self, parent) -> None:
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["bg_card"],
            corner_radius=18,
            border_width=1,
            border_color=COLORS["border"],
        )
        card.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="nsew")

        ctk.CTkLabel(card, text="🔴", font=("Segoe UI Emoji", 36)).pack(pady=(22, 8))
        ctk.CTkFrame(card, height=2, fg_color=COLORS["danger"], corner_radius=0).pack(fill="x", padx=26, pady=(2, 10))
        ctk.CTkLabel(card, text="Reporte de Riesgo", font=("Segoe UI", 15, "bold"),
                     text_color=COLORS["text_primary"]).pack()
        ctk.CTkLabel(
            card,
            text="Lista los estudiantes en riesgo medio o alto con alertas y datos clave.",
            font=FONTS["body_sm"],
            text_color=COLORS["text_secondary"],
            justify="center",
            wraplength=260,
        ).pack(pady=(8, 16), padx=16)
        ActionButton(card, "🔴 Reporte de Riesgo", style="danger",
                     command=self._generar_reporte_riesgo).pack(pady=(0, 20))

    def _generar_reporte_general(self) -> None:
        self._run_async(self._do_reporte_general, "Generando reporte general...")

    def _do_reporte_general(self) -> str:
        try:
            svc = self._app.services
            todos = svc["estudiantes"].listar_todos()
            activos = svc["estudiantes"].listar_activos()
            indicadores = svc["indicadores"].calcular_lote(
                [e.to_dict() for e in activos]
            )
            resumen = svc["indicadores"].resumen_global(indicadores)
            estudiante_ids = [int(e.id) for e in activos if getattr(e, "id", None)]
            asistencia_promedio = svc["asistencia"].promedio_asistencia_global(estudiante_ids=estudiante_ids)
            promedio_academico = svc["rendimiento"].promedio_global(estudiante_ids=estudiante_ids)
            dest = svc["reportes"].reporte_general(
                indicadores,
                resumen,
                total_estudiantes=len(todos),
                activos_count=len(activos),
                promedio_academico_global=promedio_academico,
                asistencia_promedio_global=asistencia_promedio,
            )
            return f"✅ Reporte general guardado: {dest.name}"
        except Exception as exc:
            from utils.logger import logger
            logger.exception("Error generando reporte general: %s", exc)
            return f"❌ Error generando reporte general: {exc}"

    def _generar_reporte_riesgo(self) -> None:
        self._run_async(self._do_reporte_riesgo, "Generando reporte de riesgo...")

    def _do_reporte_riesgo(self) -> str:
        try:
            svc = self._app.services
            todos = svc["estudiantes"].listar_todos()
            activos = svc["estudiantes"].listar_activos()
            indicadores = svc["indicadores"].calcular_lote(
                [e.to_dict() for e in activos]
            )
            en_riesgo = svc["indicadores"].estudiantes_en_riesgo(indicadores)
            resumen = svc["indicadores"].resumen_global(en_riesgo) if en_riesgo else {}
            estudiante_ids_en_riesgo = [int(i.estudiante_id) for i in en_riesgo] if en_riesgo else []
            asistencia_promedio = (
                svc["asistencia"].promedio_asistencia_global(estudiante_ids=estudiante_ids_en_riesgo)
                if estudiante_ids_en_riesgo else 0.0
            )
            promedio_academico = (
                svc["rendimiento"].promedio_global(estudiante_ids=estudiante_ids_en_riesgo)
                if estudiante_ids_en_riesgo else 0.0
            )
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = svc["reportes"].reporte_general(
                en_riesgo,
                resumen,
                filename=f"reporte_riesgo_{ts}.pdf",
                total_estudiantes=len(todos),
                activos_count=len(activos),
                promedio_academico_global=promedio_academico,
                asistencia_promedio_global=asistencia_promedio,
            )
            return f"✅ Reporte de riesgo guardado: {dest.name}  ({len(en_riesgo)} estudiantes)"
        except Exception as exc:
            from utils.logger import logger
            logger.exception("Error generando reporte de riesgo: %s", exc)
            return f"❌ Error generando reporte de riesgo: {exc}"

    def _exportar_excel(self) -> None:
        self._run_async(self._do_exportar_excel, "Exportando Excel...")

    def _do_exportar_excel(self) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = EXPORTS_DIR / f"becados_export_{ts}.xlsx"
        self._app.services["excel"].export_all_excel(dest)
        return f"✅ Excel exportado: {dest.name}"

    def _exportar_csv_est(self) -> None:
        self._run_async(
            lambda: self._do_csv("Estudiantes", "estudiantes"),
            "Exportando CSV...",
        )

    def _exportar_csv_asi(self) -> None:
        self._run_async(
            lambda: self._do_csv("Asistencias", "asistencias"),
            "Exportando CSV...",
        )

    def _exportar_csv_seg(self) -> None:
        self._run_async(
            lambda: self._do_csv("Seguimientos", "seguimientos"),
            "Exportando CSV...",
        )

    def _do_csv(self, sheet: str, nombre: str) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = EXPORTS_DIR / f"{nombre}_{ts}.csv"
        self._app.services["excel"].export_sheet_csv(sheet, dest)
        return f"✅ CSV exportado: {dest.name}"

    def _crear_backup(self) -> None:
        self._run_async(self._do_backup, "Creando backup...")

    def _do_backup(self) -> str:
        dest = self._app.services["excel"].backup()
        return f"✅ Backup creado: {dest.name}"

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _run_async(self, fn, msg: str = "Procesando...") -> None:
        self._log("⏳ " + msg, COLORS["text_secondary"])

        def _worker() -> None:
            try:
                result = fn()
                self.after(0, lambda: self._mostrar_aviso(result))
            except Exception as exc:
                self.after(0, lambda exc=exc: self._log(f"❌ Error: {exc}", COLORS["danger"]))

        threading.Thread(target=_worker, daemon=True).start()

    def _mostrar_aviso(self, msg: str) -> None:
        dlg = ctk.CTkToplevel(self)
        dlg.title("Operación completada")
        dlg.geometry("440x150")
        dlg.grab_set()
        ctk.CTkLabel(
            dlg,
            text=msg,
            font=FONTS["body"],
            text_color=COLORS["success"],
            wraplength=380,
            justify="center",
        ).pack(pady=24)
        ActionButton(dlg, "OK", command=dlg.destroy).pack()

    def _log(self, msg: str, color: str = COLORS["text_primary"]) -> None:
        for w in self._log_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self._log_frame, text=msg,
            font=FONTS["body"], text_color=color,
        ).pack(anchor="w", padx=4)
