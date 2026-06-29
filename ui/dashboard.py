"""Vista del Dashboard principal con KPIs y gráficos."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

import customtkinter as ctk
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

from config import COLORS, FONTS
from ui.components.cards import KPICard, RiskBadge, SectionHeader

if TYPE_CHECKING:
    from ui.app import App


class DashboardView(ctk.CTkFrame):
    """Panel principal del sistema."""

    def __init__(self, master, app: "App", **kwargs) -> None:
        super().__init__(master, fg_color=COLORS["bg_main"], **kwargs)
        self._app = app
        self._canvas_fig = None
        self._build()

    def _build(self) -> None:
        # Barra superior
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], height=64, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text="Dashboard",
            font=FONTS["heading_lg"],
            text_color=COLORS["text_primary"],
        ).pack(side="left", padx=24, pady=16)
        ctk.CTkButton(
            header, text="🔄  Actualizar",
            width=120, height=36,
            font=FONTS["body_sm"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_dark"],
            corner_radius=8,
            command=self.refresh,
        ).pack(side="right", padx=24)

        # Contenido scrollable
        self._scroll = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_main"])
        self._scroll.pack(fill="both", expand=True, padx=20, pady=16)

        self._kpi_frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._kpi_frame.pack(fill="x", pady=(0, 16))

        self._charts_frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._charts_frame.pack(fill="x", pady=(0, 16))

        self._riesgo_frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._riesgo_frame.pack(fill="x")

        self.refresh()

    def refresh(self) -> None:
        """Recarga todos los datos del dashboard."""
        threading.Thread(target=self._load_data, daemon=True).start()

    def _load_data(self) -> None:
        try:
            svc = self._app.services
            est_stats = svc["estudiantes"].estadisticas_generales()
            todos_est = svc["estudiantes"].listar_todos()

            indicadores = svc["indicadores"].calcular_lote(
                [e.to_dict() for e in todos_est[:50]]  # limitar para rendimiento
            )
            resumen = svc["indicadores"].resumen_global(indicadores)
            top = svc["indicadores"].top_estudiantes(indicadores, 5)
            en_riesgo = svc["indicadores"].estudiantes_en_riesgo(indicadores)

            pct_asi = svc["asistencia"].promedio_asistencia_global()
            pct_vol = svc["voluntariado"].promedio_horas_global()
            total_seg = svc["seguimiento"].total_seguimientos_global()
            prom_aca = svc["rendimiento"].promedio_global()

            self.after(0, lambda: self._render(
                est_stats, resumen, top, en_riesgo,
                pct_asi, pct_vol, total_seg, prom_aca, indicadores,
            ))
        except Exception as exc:
            self.after(0, lambda: self._show_error(str(exc)))

    def _render(self, est_stats, resumen, top, en_riesgo,
                pct_asi, pct_vol, total_seg, prom_aca, indicadores) -> None:
        self._render_kpis(est_stats, pct_asi, pct_vol, total_seg, prom_aca, resumen)
        self._render_charts(indicadores)
        self._render_riesgo(en_riesgo, top)

    def _render_kpis(self, est_stats, pct_asi, pct_vol, total_seg, prom_aca, resumen) -> None:
        for w in self._kpi_frame.winfo_children():
            w.destroy()

        SectionHeader(self._kpi_frame, "Indicadores Clave").pack(fill="x", pady=(0, 12))

        cards_data = [
            ("Total Becados", str(est_stats["total"]), "Estudiantes registrados", "👥", COLORS["primary"]),
            ("Activos", str(est_stats["activos"]), "En programa activo", "✅", COLORS["success"]),
            ("Asistencia Prom.", f"{pct_asi:.1f}%", "Promedio general", "📅", COLORS["info"]),
            ("Promedio Acad.", f"{prom_aca:.2f}", "Calificación promedio", "📚", COLORS["warning"]),
            ("Voluntariado", f"{pct_vol:.1f}h", "Horas por estudiante", "🤝", "#8B5CF6"),
            ("Seguimientos", str(total_seg), "Total realizados", "💬", "#EC4899"),
            ("En Riesgo Alto", str(resumen.get("en_riesgo_alto", 0)), "Requieren atención", "🔴", COLORS["danger"]),
            ("En Riesgo Medio", str(resumen.get("en_riesgo_medio", 0)), "Monitorear", "🟡", COLORS["warning"]),
        ]

        grid = ctk.CTkFrame(self._kpi_frame, fg_color="transparent")
        grid.pack(fill="x")

        for i, (title, value, sub, icon, color) in enumerate(cards_data):
            card = KPICard(
                grid, title=title, value=value,
                subtitle=sub, icon=icon, accent_color=color,
                width=180,
            )
            card.grid(row=i // 4, column=i % 4, padx=8, pady=8, sticky="ew")
            grid.grid_columnconfigure(i % 4, weight=1)

    def _render_charts(self, indicadores) -> None:
        for w in self._charts_frame.winfo_children():
            w.destroy()

        SectionHeader(self._charts_frame, "Análisis Visual").pack(fill="x", pady=(0, 12))

        chart_container = ctk.CTkFrame(self._charts_frame, fg_color="transparent")
        chart_container.pack(fill="x")
        chart_container.grid_columnconfigure(0, weight=1)
        chart_container.grid_columnconfigure(1, weight=1)

        self._chart_riesgo_dist(chart_container, indicadores)
        self._chart_asistencia(chart_container, indicadores)

    def _chart_riesgo_dist(self, parent, indicadores) -> None:
        frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=12,
                             border_width=1, border_color=COLORS["border"])
        frame.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        ctk.CTkLabel(frame, text="Distribución de Riesgo",
                     font=FONTS["heading_sm"], text_color=COLORS["text_primary"]).pack(
            anchor="w", padx=16, pady=(12, 0))

        bajo = sum(1 for i in indicadores if i.nivel_riesgo == "Bajo")
        medio = sum(1 for i in indicadores if i.nivel_riesgo == "Medio")
        alto = sum(1 for i in indicadores if i.nivel_riesgo == "Alto")

        fig, ax = plt.subplots(figsize=(4, 3), facecolor="white")
        if bajo + medio + alto > 0:
            wedges, texts, autotexts = ax.pie(
                [bajo, medio, alto],
                labels=["Bajo", "Medio", "Alto"],
                colors=["#10B981", "#F59E0B", "#EF4444"],
                autopct="%1.0f%%",
                startangle=90,
                textprops={"fontsize": 9},
            )
        ax.set_title("")
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        plt.close(fig)

    def _chart_asistencia(self, parent, indicadores) -> None:
        frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=12,
                             border_width=1, border_color=COLORS["border"])
        frame.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

        ctk.CTkLabel(frame, text="Distribución de Asistencia",
                     font=FONTS["heading_sm"], text_color=COLORS["text_primary"]).pack(
            anchor="w", padx=16, pady=(12, 0))

        buckets = {"<60%": 0, "60-75%": 0, "75-90%": 0, ">90%": 0}
        for ind in indicadores:
            p = ind.pct_asistencia
            if p < 60:
                buckets["<60%"] += 1
            elif p < 75:
                buckets["60-75%"] += 1
            elif p < 90:
                buckets["75-90%"] += 1
            else:
                buckets[">90%"] += 1

        fig, ax = plt.subplots(figsize=(4, 3), facecolor="white")
        ax.bar(
            list(buckets.keys()), list(buckets.values()),
            color=["#EF4444", "#F59E0B", "#3B82F6", "#10B981"],
            edgecolor="white", linewidth=0.5,
        )
        ax.set_ylabel("Estudiantes", fontsize=8)
        ax.tick_params(labelsize=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        plt.close(fig)

    def _render_riesgo(self, en_riesgo, top) -> None:
        for w in self._riesgo_frame.winfo_children():
            w.destroy()

        container = ctk.CTkFrame(self._riesgo_frame, fg_color="transparent")
        container.pack(fill="x")
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

        # Panel alertas
        alertas_frame = ctk.CTkFrame(container, fg_color=COLORS["bg_card"],
                                     corner_radius=12, border_width=1, border_color=COLORS["border"])
        alertas_frame.grid(row=0, column=0, padx=(0, 8), sticky="nsew", pady=(0, 16))

        ctk.CTkLabel(alertas_frame, text="🚨 Alertas — Estudiantes en Riesgo",
                     font=FONTS["heading_sm"], text_color=COLORS["danger"]).pack(
            anchor="w", padx=16, pady=(12, 8))

        if not en_riesgo:
            ctk.CTkLabel(alertas_frame, text="✅ Sin alertas activas",
                         font=FONTS["body"], text_color=COLORS["success"]).pack(padx=16, pady=16)
        else:
            for ind in en_riesgo[:8]:
                row = ctk.CTkFrame(alertas_frame, fg_color=COLORS["bg_main"], corner_radius=6)
                row.pack(fill="x", padx=12, pady=3)
                ctk.CTkLabel(row, text=ind.nombre[:28],
                             font=FONTS["body_sm"],
                             text_color=COLORS["text_primary"]).pack(side="left", padx=10, pady=6)
                RiskBadge(row, ind.nivel_riesgo).pack(side="right", padx=10)

        # Panel top estudiantes
        top_frame = ctk.CTkFrame(container, fg_color=COLORS["bg_card"],
                                 corner_radius=12, border_width=1, border_color=COLORS["border"])
        top_frame.grid(row=0, column=1, padx=(8, 0), sticky="nsew", pady=(0, 16))

        ctk.CTkLabel(top_frame, text="⭐ Top Estudiantes",
                     font=FONTS["heading_sm"], text_color=COLORS["primary"]).pack(
            anchor="w", padx=16, pady=(12, 8))

        for rank, ind in enumerate(top, 1):
            row = ctk.CTkFrame(top_frame, fg_color=COLORS["bg_main"], corner_radius=6)
            row.pack(fill="x", padx=12, pady=3)
            ctk.CTkLabel(row, text=f"#{rank}",
                         font=FONTS["heading_sm"],
                         text_color=COLORS["primary"]).pack(side="left", padx=10, pady=6)
            ctk.CTkLabel(row, text=ind.nombre[:28],
                         font=FONTS["body_sm"],
                         text_color=COLORS["text_primary"]).pack(side="left")
            RiskBadge(row, ind.nivel_riesgo).pack(side="right", padx=10)

    def _show_error(self, msg: str) -> None:
        ctk.CTkLabel(self._scroll, text=f"Error cargando datos: {msg}",
                     text_color=COLORS["danger"]).pack()

    def _build(self) -> None:
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], height=64, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header,
            text="Dashboard",
            font=FONTS["heading_lg"],
            text_color=COLORS["text_primary"],
        ).pack(side="left", padx=24, pady=16)
        ctk.CTkButton(
            header,
            text="🔄  Actualizar",
            width=120,
            height=36,
            font=FONTS["body_sm"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_dark"],
            corner_radius=8,
            command=self.refresh,
        ).pack(side="right", padx=24)

        self._scroll = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_main"])
        self._scroll.pack(fill="both", expand=True, padx=20, pady=16)

        self._kpi_frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._kpi_frame.pack(fill="x", pady=(0, 16))
        SectionHeader(self._kpi_frame, "Indicadores Clave").pack(fill="x", pady=(0, 12))
        self._kpi_grid = ctk.CTkFrame(self._kpi_frame, fg_color="transparent")
        self._kpi_grid.pack(fill="x")
        for col in range(4):
            self._kpi_grid.grid_columnconfigure(col, weight=1)

        self._kpi_cards = []
        for row_idx, card_data in enumerate([
            ("Total Becados", "0", "Estudiantes registrados", "👥", COLORS["primary"]),
            ("Activos", "0", "En programa activo", "✅", COLORS["success"]),
            ("Asistencia Prom.", "0.0%", "Promedio general", "📅", COLORS["info"]),
            ("Promedio Acad.", "0.00", "Calificación promedio", "📚", COLORS["warning"]),
            ("Voluntariado", "0.0h", "Horas por estudiante", "🤝", "#8B5CF6"),
            ("Seguimientos", "0", "Total realizados", "💬", "#EC4899"),
            ("En Riesgo Alto", "0", "Requieren atención", "🔴", COLORS["danger"]),
            ("En Riesgo Medio", "0", "Monitorear", "🟡", COLORS["warning"]),
        ]):
            card = KPICard(
                self._kpi_grid,
                title=card_data[0],
                value=card_data[1],
                subtitle=card_data[2],
                icon=card_data[3],
                accent_color=card_data[4],
                width=180,
            )
            card.grid(row=row_idx // 4, column=row_idx % 4, padx=8, pady=8, sticky="ew")
            self._kpi_cards.append(card)

        self._charts_frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._charts_frame.pack(fill="x", pady=(0, 16))
        SectionHeader(self._charts_frame, "Análisis Visual").pack(fill="x", pady=(0, 12))
        chart_container = ctk.CTkFrame(self._charts_frame, fg_color="transparent")
        chart_container.pack(fill="x")
        chart_container.grid_columnconfigure(0, weight=1)
        chart_container.grid_columnconfigure(1, weight=1)

        self._chart_riesgo_frame, self._chart_riesgo_fig, self._chart_riesgo_ax, self._chart_riesgo_canvas = self._create_chart_panel(
            chart_container,
            0,
            0,
            "Distribución de Riesgo",
        )
        self._chart_asistencia_frame, self._chart_asistencia_fig, self._chart_asistencia_ax, self._chart_asistencia_canvas = self._create_chart_panel(
            chart_container,
            0,
            1,
            "Distribución de Asistencia",
        )

        self._riesgo_frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._riesgo_frame.pack(fill="x")
        self._risk_container = ctk.CTkFrame(self._riesgo_frame, fg_color="transparent")
        self._risk_container.pack(fill="x")
        self._risk_container.grid_columnconfigure(0, weight=1)
        self._risk_container.grid_columnconfigure(1, weight=1)

        self._alertas_frame = ctk.CTkFrame(
            self._risk_container,
            fg_color=COLORS["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        self._alertas_frame.grid(row=0, column=0, padx=(0, 8), sticky="nsew", pady=(0, 16))
        ctk.CTkLabel(
            self._alertas_frame,
            text="🚨 Alertas — Estudiantes en Riesgo",
            font=FONTS["heading_sm"],
            text_color=COLORS["danger"],
        ).pack(anchor="w", padx=16, pady=(12, 8))
        self._alert_empty_label = ctk.CTkLabel(
            self._alertas_frame,
            text="✅ Sin alertas activas",
            font=FONTS["body"],
            text_color=COLORS["success"],
        )
        self._alert_empty_label.pack(padx=16, pady=16)
        self._alert_rows = []
        for _ in range(8):
            row = ctk.CTkFrame(self._alertas_frame, fg_color=COLORS["bg_main"], corner_radius=6)
            name = ctk.CTkLabel(row, text="", font=FONTS["body_sm"], text_color=COLORS["text_primary"])
            badge_slot = ctk.CTkFrame(row, fg_color="transparent")
            name.pack(side="left", padx=10, pady=6)
            badge_slot.pack(side="right", padx=10, pady=3)
            self._alert_rows.append({"row": row, "name": name, "badge_slot": badge_slot})

        self._top_frame = ctk.CTkFrame(
            self._risk_container,
            fg_color=COLORS["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        self._top_frame.grid(row=0, column=1, padx=(8, 0), sticky="nsew", pady=(0, 16))
        ctk.CTkLabel(
            self._top_frame,
            text="⭐ Top Estudiantes",
            font=FONTS["heading_sm"],
            text_color=COLORS["primary"],
        ).pack(anchor="w", padx=16, pady=(12, 8))
        self._top_rows = []
        for _ in range(5):
            row = ctk.CTkFrame(self._top_frame, fg_color=COLORS["bg_main"], corner_radius=6)
            rank = ctk.CTkLabel(row, text="", font=FONTS["heading_sm"], text_color=COLORS["primary"])
            name = ctk.CTkLabel(row, text="", font=FONTS["body_sm"], text_color=COLORS["text_primary"])
            rank.pack(side="left", padx=10, pady=6)
            name.pack(side="left")
            self._top_rows.append({"row": row, "rank": rank, "name": name})

    def refresh(self, on_complete=None) -> None:
        self._ready_callback = on_complete
        threading.Thread(target=self._load_data, daemon=True).start()

    def _create_chart_panel(self, parent, row: int, column: int, title: str):
        frame = ctk.CTkFrame(
            parent,
            fg_color=COLORS["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        frame.grid(row=row, column=column, padx=(0, 8) if column == 0 else (8, 0), sticky="nsew")
        ctk.CTkLabel(
            frame,
            text=title,
            font=FONTS["heading_sm"],
            text_color=COLORS["text_primary"],
        ).pack(anchor="w", padx=16, pady=(12, 0))
        fig, ax = plt.subplots(figsize=(4, 3), facecolor="white")
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        canvas.draw()
        return frame, fig, ax, canvas

    def _load_data(self) -> None:
        try:
            svc = self._app.services
            est_stats = svc["estudiantes"].estadisticas_generales()
            todos_est = svc["estudiantes"].listar_todos()

            indicadores = svc["indicadores"].calcular_lote(
                [e.to_dict() for e in todos_est[:50]]
            )
            resumen = svc["indicadores"].resumen_global(indicadores)
            top = svc["indicadores"].top_estudiantes(indicadores, 5)
            en_riesgo = svc["indicadores"].estudiantes_en_riesgo(indicadores)

            pct_asi = svc["asistencia"].promedio_asistencia_global()
            pct_vol = svc["voluntariado"].promedio_horas_global()
            total_seg = svc["seguimiento"].total_seguimientos_global()
            prom_aca = svc["rendimiento"].promedio_global()

            self.after(
                0,
                lambda: self._render(
                    est_stats,
                    resumen,
                    top,
                    en_riesgo,
                    pct_asi,
                    pct_vol,
                    total_seg,
                    prom_aca,
                    indicadores,
                ),
            )
        except Exception as exc:
            self.after(0, lambda: self._show_error(str(exc)))

    def _render(self, est_stats, resumen, top, en_riesgo,
                pct_asi, pct_vol, total_seg, prom_aca, indicadores) -> None:
        cards_data = [
            ("Total Becados", str(est_stats["total"]), "Estudiantes registrados", "👥", COLORS["primary"]),
            ("Activos", str(est_stats["activos"]), "En programa activo", "✅", COLORS["success"]),
            ("Asistencia Prom.", f"{pct_asi:.1f}%", "Promedio general", "📅", COLORS["info"]),
            ("Promedio Acad.", f"{prom_aca:.2f}", "Calificación promedio", "📚", COLORS["warning"]),
            ("Voluntariado", f"{pct_vol:.1f}h", "Horas por estudiante", "🤝", "#8B5CF6"),
            ("Seguimientos", str(total_seg), "Total realizados", "💬", "#EC4899"),
            ("En Riesgo Alto", str(resumen.get("en_riesgo_alto", 0)), "Requieren atención", "🔴", COLORS["danger"]),
            ("En Riesgo Medio", str(resumen.get("en_riesgo_medio", 0)), "Monitorear", "🟡", COLORS["warning"]),
        ]
        for card, data in zip(self._kpi_cards, cards_data):
            card.update_card(*data)

        self._chart_riesgo_ax.clear()
        self._chart_asistencia_ax.clear()

        bajo = sum(1 for i in indicadores if i.nivel_riesgo == "Bajo")
        medio = sum(1 for i in indicadores if i.nivel_riesgo == "Medio")
        alto = sum(1 for i in indicadores if i.nivel_riesgo == "Alto")
        if bajo + medio + alto > 0:
            self._chart_riesgo_ax.pie(
                [bajo, medio, alto],
                labels=["Bajo", "Medio", "Alto"],
                colors=["#10B981", "#F59E0B", "#EF4444"],
                autopct="%1.0f%%",
                startangle=90,
                textprops={"fontsize": 9},
            )
        self._chart_riesgo_ax.set_title("")
        self._chart_riesgo_fig.tight_layout()

        buckets = {"<60%": 0, "60-75%": 0, "75-90%": 0, ">90%": 0}
        for ind in indicadores:
            p = ind.pct_asistencia
            if p < 60:
                buckets["<60%"] += 1
            elif p < 75:
                buckets["60-75%"] += 1
            elif p < 90:
                buckets["75-90%"] += 1
            else:
                buckets[">90%"] += 1

        self._chart_asistencia_ax.bar(
            list(buckets.keys()),
            list(buckets.values()),
            color=["#EF4444", "#F59E0B", "#3B82F6", "#10B981"],
            edgecolor="white",
            linewidth=0.5,
        )
        self._chart_asistencia_ax.set_ylabel("Estudiantes", fontsize=8)
        self._chart_asistencia_ax.tick_params(labelsize=8)
        self._chart_asistencia_ax.spines["top"].set_visible(False)
        self._chart_asistencia_ax.spines["right"].set_visible(False)
        self._chart_asistencia_fig.tight_layout()

        self._chart_riesgo_canvas.draw_idle()
        self._chart_asistencia_canvas.draw_idle()

        if hasattr(self, "_alert_empty_label"):
            if en_riesgo:
                self._alert_empty_label.pack_forget()
            else:
                self._alert_empty_label.pack(padx=16, pady=16)

        for idx, entry in enumerate(self._alert_rows):
            if idx < len(en_riesgo):
                indicador = en_riesgo[idx]
                if not entry["row"].winfo_manager():
                    entry["row"].pack(fill="x", padx=12, pady=3)
                entry["name"].configure(text=indicador.nombre[:28])
                for child in entry["badge_slot"].winfo_children():
                    child.destroy()
                RiskBadge(entry["badge_slot"], indicador.nivel_riesgo).pack()
            else:
                entry["name"].configure(text="")
                for child in entry["badge_slot"].winfo_children():
                    child.destroy()
                entry["row"].pack_forget()

        for idx, entry in enumerate(self._top_rows):
            if idx < len(top):
                indicador = top[idx]
                if not entry["row"].winfo_manager():
                    entry["row"].pack(fill="x", padx=12, pady=3)
                entry["rank"].configure(text=f"#{idx + 1}")
                entry["name"].configure(text=indicador.nombre[:28])
            else:
                entry["row"].pack_forget()
                entry["rank"].configure(text="")
                entry["name"].configure(text="")

        if self._ready_callback:
            callback = self._ready_callback
            self._ready_callback = None
            self.after_idle(callback)

    def _show_error(self, msg: str) -> None:
        if hasattr(self, "_scroll"):
            ctk.CTkLabel(
                self._scroll,
                text=f"Error cargando datos: {msg}",
                text_color=COLORS["danger"],
            ).pack()
        if self._ready_callback:
            callback = self._ready_callback
            self._ready_callback = None
            self.after_idle(callback)
