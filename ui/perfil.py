"""Vista de perfil completo del estudiante."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Optional

import customtkinter as ctk
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

from config import COLORS, FONTS
from services.estudiantes import Estudiante
from services.indicadores import IndicadorEstudiante
from ui.components.cards import KPICard, RiskBadge, ActionButton, SectionHeader
from ui.seguimiento import FormularioSeguimiento
from ui.asistencia import FormularioAsistencia
from ui.voluntariado import FormularioVoluntariado

if TYPE_CHECKING:
    from ui.app import App


class PerfilEstudianteView(ctk.CTkToplevel):
    """Ventana de perfil completo del estudiante."""

    def __init__(self, master: "App", estudiante_id: int) -> None:
        super().__init__(master)
        self.withdraw()
        self._app = master
        self._id = estudiante_id
        self.title("Perfil del Estudiante")
        self.geometry("1100x720")
        self.configure(fg_color=COLORS["bg_main"])
        self._build_loading()
        threading.Thread(target=self._load, daemon=True).start()

    def _build_loading(self) -> None:
        ctk.CTkLabel(self, text="⏳ Cargando perfil...",
                     font=FONTS["heading_md"],
                     text_color=COLORS["text_secondary"]).pack(expand=True)

    def _load(self) -> None:
        try:
            svc = self._app.services
            est = svc["estudiantes"].obtener_por_id(self._id)
            if not est:
                self.after(0, lambda: self._show_error("Estudiante no encontrado."))
                return

            ind = svc["indicadores"].calcular(self._id, est.nombre_completo)
            asi_stats = svc["asistencia"].calcular_estadisticas(self._id)
            vol_stats = svc["voluntariado"].calcular_estadisticas(self._id)
            seg_stats = svc["seguimiento"].calcular_estadisticas(self._id)
            ren_stats = svc["rendimiento"].calcular_estadisticas(self._id)

            seg_hist_df = svc["seguimiento"].historial_dataframe(self._id)
            asi_hist_df = svc["asistencia"].historial_dataframe(self._id)

            self.after(0, lambda: self._render(
                est, ind, asi_stats, vol_stats, seg_stats, ren_stats,
                seg_hist_df, asi_hist_df,
            ))
        except Exception as exc:
            self.after(0, lambda exc=exc: self._show_error(str(exc)))

    def _render(self, est, ind, asi_stats, vol_stats, seg_stats,
                ren_stats, seg_hist_df, asi_hist_df) -> None:
        # Limpiar loading
        for w in self.winfo_children():
            w.destroy()

        # Header del perfil
        hdr = ctk.CTkFrame(self, fg_color=COLORS["primary"], corner_radius=0, height=100)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        ctk.CTkLabel(hdr, text="👤", font=("Segoe UI Emoji", 36),
                     text_color="white").pack(side="left", padx=20)
        info_hdr = ctk.CTkFrame(hdr, fg_color="transparent")
        info_hdr.pack(side="left", pady=10)
        ctk.CTkLabel(info_hdr, text=est.nombre_completo,
                     font=FONTS["heading_lg"], text_color="white").pack(anchor="w")
        ctk.CTkLabel(info_hdr,
                     text=f"{est.codigo}  •  {est.universidad}  •  {est.carrera}",
                     font=FONTS["body_sm"], text_color="white").pack(anchor="w")

        # Nivel de riesgo en header
        risk_hdr = ctk.CTkFrame(info_hdr, fg_color="transparent")
        risk_hdr.pack(anchor="w", pady=(8, 0))
        ctk.CTkLabel(risk_hdr, text="Nivel de Riesgo",
                     font=FONTS["caption"], text_color="white").pack(side="left")
        RiskBadge(risk_hdr, ind.nivel_riesgo).pack(side="left", padx=(8, 0))

        # Botones de acción rápida
        actions = ctk.CTkFrame(hdr, fg_color="transparent")
        actions.pack(side="right", padx=12)
        ActionButton(actions, "💬 Seguimiento", style="ghost_light",
                     command=lambda: FormularioSeguimiento(
                         self, on_save=self._reload, estudiante_id=self._id)).pack(side="left", padx=4,pady=2)
        ActionButton(actions, "✅ Asistencia", style="ghost_light",
                     command=lambda: FormularioAsistencia(
                         self, on_save=self._reload, estudiante_id=self._id)).pack(side="left", padx=4, pady=2)
        ActionButton(actions, "🤝 Voluntariado", style="ghost_light",
                     command=lambda: FormularioVoluntariado(
                         self, on_save=self._reload, estudiante_id=self._id)).pack(side="left", padx=4,pady=2)

        # Generar reporte
        ActionButton(hdr, "📄 PDF", style="secondary",
                     command=lambda: self._generar_reporte(
                         est, ind, asi_stats, vol_stats, seg_stats, ren_stats,
                         seg_hist_df.to_dict("records") if not seg_hist_df.empty else [],
                     )).pack(side="right", padx=8)

        # Contenido principal scrollable
        main_scroll = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_main"])
        main_scroll.pack(fill="both", expand=True, padx=20, pady=16)

        # ── KPIs ─────────────────────────────────────────────────────────────
        SectionHeader(main_scroll, "Indicadores").pack(fill="x", pady=(0, 12))

        kpi_grid = ctk.CTkFrame(main_scroll, fg_color="transparent")
        kpi_grid.pack(fill="x", pady=(0, 16))

        kpis = [
            ("Asistencia", f"{asi_stats['pct_asistencia']:.1f}%",
             f"{asi_stats['presentes']} presentes / {asi_stats['total']} total",
             "📅", COLORS["info"]),
            ("Inasistencias", f"{asi_stats['pct_inasistencia']:.1f}%",
             f"{asi_stats['ausentes']} ausencias registradas",
             "❌", COLORS["danger"]),
            ("Voluntariado", f"{vol_stats['horas_acumuladas']:.1f}h",
             f"{vol_stats['pct_cumplimiento']:.0f}% de meta (40h)",
             "🤝", COLORS["success"]),
            ("Promedio", f"{ren_stats['promedio']:.2f}",
             f"{ren_stats['materias_aprobadas']} aprobadas / {ren_stats['materias_reprobadas']} reprobadas",
             "📚", COLORS["warning"]),
            ("Seguimientos", str(seg_stats["total"]),
             f"Último hace {seg_stats['dias_sin_seguimiento']} días",
             "💬", "#8B5CF6"),
            ("Índice Riesgo", f"{ind.indice_riesgo:.1%}",
             f"{ind.emoji_riesgo} Nivel {ind.nivel_riesgo}",
             "⚠️", COLORS["danger"] if ind.nivel_riesgo == "Alto" else COLORS["warning"]),
        ]
        for i, (title, val, sub, icon, color) in enumerate(kpis):
            card = KPICard(kpi_grid, title=title, value=val, subtitle=sub,
                           icon=icon, accent_color=color)
            card.grid(row=i // 3, column=i % 3, padx=8, pady=8, sticky="ew")
            kpi_grid.grid_columnconfigure(i % 3, weight=1)

        # ── Alertas ───────────────────────────────────────────────────────────
        if ind.alertas:
            alert_f = ctk.CTkFrame(main_scroll, fg_color="#FEF2F2",
                                   corner_radius=10, border_width=1,
                                   border_color="#FECACA")
            alert_f.pack(fill="x", pady=(0, 16))
            ctk.CTkLabel(alert_f, text="🚨 Alertas Activas",
                         font=FONTS["heading_sm"],
                         text_color=COLORS["danger"]).pack(anchor="w", padx=16, pady=(10, 4))
            for alerta in ind.alertas:
                ctk.CTkLabel(alert_f, text=alerta,
                             font=FONTS["body_sm"],
                             text_color=COLORS["danger"]).pack(anchor="w", padx=24, pady=2)
            ctk.CTkFrame(alert_f, height=8, fg_color="transparent").pack()

        # ── Gráficos ──────────────────────────────────────────────────────────
        SectionHeader(main_scroll, "Análisis Gráfico").pack(fill="x", pady=(0, 12))

        charts_grid = ctk.CTkFrame(main_scroll, fg_color="transparent")
        charts_grid.pack(fill="x", pady=(0, 16))
        charts_grid.grid_columnconfigure(0, weight=1)
        charts_grid.grid_columnconfigure(1, weight=1)

        self._chart_radar(charts_grid, ind)
        self._chart_asistencia_mensual(charts_grid, asi_hist_df)

        # ── Info general ──────────────────────────────────────────────────────
        SectionHeader(main_scroll, "Información Personal").pack(fill="x", pady=(0, 12))

        info_grid = ctk.CTkFrame(main_scroll, fg_color=COLORS["bg_card"],
                                  corner_radius=12, border_width=1, border_color=COLORS["border"])
        info_grid.pack(fill="x", pady=(0, 16))

        campos = [
            ("Código", est.codigo), ("Estado", est.estado),
            ("Universidad", est.universidad), ("Carrera", est.carrera),
            ("Ciclo", est.ciclo), ("Monitor", est.monitor),
            ("Correo", est.correo), ("Teléfono", est.telefono),
            ("Fecha Ingreso", est.fecha_ingreso),
        ]
        for i, (label, value) in enumerate(campos):
            row_f = ctk.CTkFrame(info_grid, fg_color="transparent")
            row_f.grid(row=i // 2, column=i % 2, padx=16, pady=6, sticky="w")
            info_grid.grid_columnconfigure(i % 2, weight=1)
            ctk.CTkLabel(row_f, text=f"{label}:", font=FONTS["body_sm"],
                         text_color=COLORS["text_secondary"]).pack(side="left", padx=(0, 6))
            ctk.CTkLabel(row_f, text=str(value or "—"), font=FONTS["body"],
                         text_color=COLORS["text_primary"]).pack(side="left")

        # ── Historial de seguimientos ─────────────────────────────────────────
        SectionHeader(main_scroll, "Historial de Seguimientos").pack(fill="x", pady=(16, 12))

        if seg_hist_df.empty:
            ctk.CTkLabel(main_scroll, text="Sin seguimientos registrados.",
                         font=FONTS["body"], text_color=COLORS["text_secondary"]).pack()
        else:
            for _, row in seg_hist_df.head(8).iterrows():
                seg_card = ctk.CTkFrame(main_scroll, fg_color=COLORS["bg_card"],
                                         corner_radius=10, border_width=1,
                                         border_color=COLORS["border"])
                seg_card.pack(fill="x", pady=4)
                top_row = ctk.CTkFrame(seg_card, fg_color="transparent")
                top_row.pack(fill="x", padx=16, pady=(10, 2))
                ctk.CTkLabel(top_row,
                             text=f"📅 {str(row.get('Fecha', ''))[:10]}  •  {row.get('Tipo', '')}",
                             font=FONTS["heading_sm"],
                             text_color=COLORS["primary"]).pack(side="left")
                ctk.CTkLabel(seg_card, text=str(row.get("Descripcion", "")),
                             font=FONTS["body_sm"],
                             text_color=COLORS["text_primary"],
                             wraplength=800, justify="left").pack(anchor="w", padx=16, pady=(0, 4))
                if row.get("AccionRealizada"):
                    ctk.CTkLabel(seg_card,
                                 text=f"✔ {row.get('AccionRealizada', '')}",
                                 font=FONTS["body_sm"],
                                 text_color=COLORS["success"]).pack(anchor="w", padx=16, pady=(0, 8))

            self.update_idletasks()
            self.deiconify()
            self.lift()

    def _chart_radar(self, parent, ind: IndicadorEstudiante) -> None:
        frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=12,
                             border_width=1, border_color=COLORS["border"])
        frame.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        ctk.CTkLabel(frame, text="Perfil de Desempeño (Radar)",
                     font=FONTS["heading_sm"], text_color=COLORS["text_primary"]).pack(
            anchor="w", padx=16, pady=(12, 0))

        categorias = ["Asistencia", "Promedio", "Voluntariado", "Seguimiento"]
        valores = [
            ind.score_asistencia,
            ind.score_promedio,
            ind.score_voluntariado,
            ind.score_seguimiento,
        ]
        N = len(categorias)
        angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
        valores_plot = valores + valores[:1]
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(4, 3.2), subplot_kw=dict(polar=True), facecolor="white")
        ax.plot(angles, valores_plot, "o-", linewidth=2, color="#2563EB")
        ax.fill(angles, valores_plot, alpha=0.25, color="#2563EB")
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categorias, size=8)
        ax.set_ylim(0, 1)
        ax.set_yticks([0.25, 0.5, 0.75, 1.0])
        ax.set_yticklabels(["25%", "50%", "75%", "100%"], size=6)
        ax.grid(color="#E2E8F0", linewidth=0.5)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        plt.close(fig)

    def _chart_asistencia_mensual(self, parent, asi_hist_df) -> None:
        frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=12,
                             border_width=1, border_color=COLORS["border"])
        frame.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
        ctk.CTkLabel(frame, text="Asistencia por Mes",
                     font=FONTS["heading_sm"], text_color=COLORS["text_primary"]).pack(
            anchor="w", padx=16, pady=(12, 0))

        fig, ax = plt.subplots(figsize=(4, 3.2), facecolor="white")
        if not asi_hist_df.empty and "Fecha" in asi_hist_df.columns:
            import pandas as pd
            df = asi_hist_df.copy()
            df["Mes"] = pd.to_datetime(df["Fecha"], errors="coerce").dt.to_period("M").astype(str)
            resumen = df.groupby(["Mes", "Estado"]).size().unstack(fill_value=0)
            meses = resumen.index.tolist()[-8:]
            presentes = resumen.get("Presente", pd.Series(dtype=int)).reindex(meses, fill_value=0)
            ausentes = resumen.get("Ausente", pd.Series(dtype=int)).reindex(meses, fill_value=0)
            x = range(len(meses))
            ax.bar(x, presentes, label="Presente", color="#10B981", alpha=0.8)
            ax.bar(x, ausentes, bottom=presentes, label="Ausente", color="#EF4444", alpha=0.8)
            ax.set_xticks(x)
            ax.set_xticklabels([m[-5:] for m in meses], rotation=45, fontsize=7)
            ax.legend(fontsize=7)
            ax.set_ylabel("Días", fontsize=8)
        else:
            ax.text(0.5, 0.5, "Sin datos", ha="center", va="center", transform=ax.transAxes)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        plt.close(fig)

    def _generar_reporte(self, est, ind, asi_stats, vol_stats, seg_stats, ren_stats, hist) -> None:
        try:
            svc_rep = self._app.services["reportes"]
            dest = svc_rep.reporte_estudiante(
                estudiante=est,
                indicador=ind,
                asi_stats=asi_stats,
                vol_stats=vol_stats,
                seg_stats=seg_stats,
                ren_stats=ren_stats,
                historial_seguimientos=hist,
            )
            dlg = ctk.CTkToplevel(self)
            dlg.title("Reporte generado")
            dlg.geometry("400x140")
            dlg.grab_set()
            ctk.CTkLabel(dlg, text=f"✅ Reporte PDF generado:\n{dest.name}",
                         font=FONTS["body"], text_color=COLORS["success"]).pack(pady=24)
            ActionButton(dlg, "OK", command=dlg.destroy).pack()
        except Exception as exc:
            dlg = ctk.CTkToplevel(self)
            dlg.geometry("400x140")
            dlg.grab_set()
            ctk.CTkLabel(dlg, text=f"Error: {exc}", text_color=COLORS["danger"],
                         font=FONTS["body"]).pack(pady=24)
            ActionButton(dlg, "OK", command=dlg.destroy).pack()

    def _reload(self) -> None:
        self.withdraw()
        for w in self.winfo_children():
            w.destroy()
        self._build_loading()
        threading.Thread(target=self._load, daemon=True).start()

    def _show_error(self, msg: str) -> None:
        for w in self.winfo_children():
            w.destroy()
        ctk.CTkLabel(self, text=f"Error: {msg}",
                     font=FONTS["body"], text_color=COLORS["danger"]).pack(expand=True)
        self.update_idletasks()
        self.deiconify()
        self.lift()
