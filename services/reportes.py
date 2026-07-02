"""
Generación de reportes PDF profesionales usando ReportLab.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from config import REPORTS_DIR, HORAS_VOLUNTARIADO_REQUERIDAS
from services.estudiantes import Estudiante
from services.indicadores import IndicadorEstudiante
from utils.logger import logger

# ── Colores corporativos ─────────────────────────────────────────────────────
AZUL = colors.HexColor("#2563EB")
AZUL_CLARO = colors.HexColor("#DBEAFE")
GRIS = colors.HexColor("#64748B")
GRIS_CLARO = colors.HexColor("#F8FAFC")
NEGRO = colors.HexColor("#0F172A")
VERDE = colors.HexColor("#10B981")
AMARILLO = colors.HexColor("#F59E0B")
ROJO = colors.HexColor("#EF4444")
BLANCO = colors.white


def _color_riesgo(nivel: str) -> colors.Color:
    return {"Bajo": VERDE, "Medio": AMARILLO, "Alto": ROJO}.get(nivel, GRIS)


class ReportesService:
    """Genera reportes PDF individuales y generales."""

    def __init__(self) -> None:
        self.styles = getSampleStyleSheet()
        self._add_custom_styles()

    def _add_custom_styles(self) -> None:
        self.styles.add(ParagraphStyle(
            "TituloReporte", parent=self.styles["Title"],
            fontSize=24, textColor=AZUL, spaceAfter=6,
            fontName="Helvetica-Bold",
            alignment=TA_CENTER,
        ))
        self.styles.add(ParagraphStyle(
            "Subtitulo", parent=self.styles["Heading2"],
            fontSize=13, textColor=NEGRO, spaceBefore=12, spaceAfter=6,
            fontName="Helvetica-Bold",
        ))
        self.styles.add(ParagraphStyle(
            "CuerpoNormal", parent=self.styles["Normal"],
            fontSize=10.5, textColor=NEGRO, leading=15,
        ))
        self.styles.add(ParagraphStyle(
            "CuerpoCentrado", parent=self.styles["Normal"],
            fontSize=10.5, textColor=NEGRO, leading=15,
            alignment=TA_CENTER,
        ))
        self.styles.add(ParagraphStyle(
            "Pie", parent=self.styles["Normal"],
            fontSize=8, textColor=GRIS, alignment=TA_CENTER,
        ))
        self.styles.add(ParagraphStyle(
            "Alerta", parent=self.styles["Normal"],
            fontSize=10, textColor=ROJO, leading=15,
        ))

    # ── Reporte individual ────────────────────────────────────────────────────

    def reporte_estudiante(
        self,
        estudiante: Estudiante,
        indicador: IndicadorEstudiante,
        asi_stats: dict,
        vol_stats: dict,
        seg_stats: dict,
        ren_stats: dict,
        historial_seguimientos: list,
        filename: Optional[str] = None,
    ) -> Path:
        """Genera PDF completo para un estudiante."""
        if not filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reporte_{estudiante.id}_{ts}.pdf"
        dest = REPORTS_DIR / filename

        doc = SimpleDocTemplate(
            str(dest),
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2.5 * cm,
            bottomMargin=2 * cm,
        )
        story = []

        # Encabezado
        story += self._encabezado(estudiante)
        story.append(HRFlowable(width="100%", thickness=2, color=AZUL, spaceAfter=12))

        # Información general
        story += self._seccion_info_general(estudiante)

        # Indicadores KPI
        story += self._seccion_kpis(indicador, asi_stats, vol_stats, ren_stats)

        # Riesgo
        story += self._seccion_riesgo(indicador)

        # Historial de seguimientos
        story += self._seccion_seguimientos(historial_seguimientos)

        # Conclusiones y recomendaciones
        story += self._seccion_recomendaciones(indicador, asi_stats, vol_stats, ren_stats)

        # Pie de página
        story.append(Spacer(1, 1 * cm))
        story.append(HRFlowable(width="100%", thickness=1, color=GRIS_CLARO, spaceAfter=6))
        story.append(Paragraph(
            f"Reporte generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} | "
            "Sistema Inteligente de Seguimiento para Estudiantes Becados",
            self.styles["Pie"],
        ))

        doc.build(story)
        logger.info("Reporte PDF generado: %s", dest)
        return dest

    def _encabezado(self, estudiante: Estudiante) -> list:
        elementos = [
            Paragraph("Sistema de Seguimiento — Estudiantes Becados", self.styles["Pie"]),
            Paragraph(f"Reporte: {estudiante.nombre_completo}", self.styles["TituloReporte"]),
            Paragraph(
                f"Código: {estudiante.codigo} &nbsp;|&nbsp; "
                f"Estado: {estudiante.estado} &nbsp;|&nbsp; "
                f"Monitor: {estudiante.monitor}",
                self.styles["CuerpoNormal"],
            ),
            Spacer(1, 0.4 * cm),
        ]
        return elementos

    def _seccion_info_general(self, e: Estudiante) -> list:
        data = [
            ["Universidad", e.universidad, "Correo", e.correo],
            ["Carrera", e.carrera, "Fecha Ingreso", e.fecha_ingreso],
            ["Ciclo", e.ciclo, "Teléfono", e.telefono],
        ]
        tabla = Table(data, colWidths=[3 * cm, 7 * cm, 3 * cm, 4 * cm])
        tabla.setStyle(TableStyle([
            # Tamaño de fuente
            ("FONTSIZE", (0, 0), (-1, -1), 9),

            # Fondo alternado para las filas
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [BLANCO, GRIS_CLARO]),

            # Columnas de etiquetas (1 y 3) en azul
            ("BACKGROUND", (0, 0), (0, -1), AZUL),
            ("BACKGROUND", (2, 0), (2, -1), AZUL),

            # Texto blanco en las columnas azules
            ("TEXTCOLOR", (0, 0), (0, -1), BLANCO),
            ("TEXTCOLOR", (2, 0), (2, -1), BLANCO),

            # Negrita en las etiquetas
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),

            # Bordes
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),

            # Alineación
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),

            # Espaciado interno
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        return [
            Paragraph("Información General", self.styles["Subtitulo"]),
            tabla,
            Spacer(1, 0.5 * cm),
        ]

    def _seccion_kpis(self, ind: IndicadorEstudiante, asi: dict, vol: dict, ren: dict) -> list:
        data = [
            ["Indicador", "Valor", "Estado"],
            ["Asistencia", f"{asi.get('pct_asistencia', 0):.1f}%",
             "OK" if asi.get('pct_asistencia', 0) >= 75 else "Bajo"],
            ["Promedio Académico", f"{ren.get('promedio', 0):.2f}",
             "OK" if ren.get('promedio', 0) >= 7 else "Bajo"],
            ["Horas Voluntariado", f"{vol.get('horas_acumuladas', 0):.1f} / 40h",
             "Cumplido" if vol.get('cumplido', False) else "Pendiente"],
            ["Días sin seguimiento", f"{ind.dias_sin_seguimiento}",
             "OK" if ind.dias_sin_seguimiento <= 30 else "Atención"],
            ["Índice de riesgo", f"{ind.indice_riesgo:.2%}", ind.nivel_riesgo],
        ]
        col_w = [6 * cm, 4 * cm, 4 * cm]
        tabla = Table(data, colWidths=col_w)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AZUL),
            ("TEXTCOLOR", (0, 0), (-1, 0), BLANCO),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BLANCO, GRIS_CLARO]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("ALIGN", (1, 0), (-1, -1), "LEFT"), 
            ("PADDING", (0, 0), (-1, -1), 7),
        ]))
        return [
            Paragraph("Indicadores de Seguimiento", self.styles["Subtitulo"]),
            tabla,
            Spacer(1, 0.5 * cm),
        ]

    def _seccion_riesgo(self, ind: IndicadorEstudiante) -> list:

        elementos = [
            Paragraph("Alertas Activas", self.styles["Subtitulo"])
        ]

        if ind.alertas:
            for alerta in ind.alertas:
                elementos.append(Paragraph(f"{alerta}", self.styles["Alerta"]))
        else:
            elementos.append(
                Paragraph(
                    "No existen alertas activas para este estudiante.",
                    self.styles["CuerpoNormal"]
                )
            )
        
        elementos.append(Spacer(1, 0.5 * cm))
        return elementos

    def _seccion_seguimientos(self, historial: list) -> list:
        if not historial:
            return [
                Paragraph("Historial de Seguimientos", self.styles["Subtitulo"]),
                Paragraph("Sin seguimientos registrados.", self.styles["CuerpoNormal"]),
                Spacer(1, 0.5 * cm),
            ]
        data = [["Fecha", "Tipo", "Descripción"]]
        for s in historial[:10]:  # máximo 10 en el reporte
            desc = str(s.get("Descripcion", "") or "")[:80]
            data.append([
                str(s.get("Fecha", ""))[:10],
                str(s.get("Tipo", "")),
                desc,
            ])
        col_w = [2.5 * cm, 3.5 * cm, 11 * cm]
        tabla = Table(data, colWidths=col_w)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AZUL),
            ("TEXTCOLOR", (0, 0), (-1, 0), BLANCO),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BLANCO, GRIS_CLARO]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        return [
            Paragraph("Historial de Seguimientos", self.styles["Subtitulo"]),
            tabla,
            Spacer(1, 0.5 * cm),
        ]

    def _seccion_recomendaciones(
        self, ind: IndicadorEstudiante, asi: dict, vol: dict, ren: dict
    ) -> list:
        recs = []
        if asi.get("pct_asistencia", 0) < 75:
            recs.append("• Reforzar asistencia: programar reunión para identificar causas de inasistencia.")
        if ren.get("promedio", 0) < 7 and ren.get("promedio", 0) > 0:
            recs.append("• Apoyar académicamente: considerar tutorías o plan de mejora académica.")
        if not vol.get("cumplido", False):
            pendiente = vol.get("horas_pendientes", 0)
            recs.append(f"• Completar voluntariado: faltan {pendiente:.0f} horas para cumplir la meta.")
        if ind.dias_sin_seguimiento > 30:
            recs.append(f"• Realizar seguimiento inmediato: llevan {ind.dias_sin_seguimiento} días sin contacto.")
        if not recs:
            recs.append("• Continuar con el seguimiento regular. El estudiante muestra buen desempeño.")

        elementos = [Paragraph("Recomendaciones", self.styles["Subtitulo"])]
        for rec in recs:
            elementos.append(Paragraph(rec, self.styles["CuerpoNormal"]))
        return elementos

    # ── Reporte general ───────────────────────────────────────────────────────

    def reporte_general(
        self,
        indicadores: list,
        resumen: dict,
        filename: Optional[str] = None,
    ) -> Path:
        """Genera reporte consolidado de todos los estudiantes."""
        if not filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reporte_general_{ts}.pdf"
        dest = REPORTS_DIR / filename

        doc = SimpleDocTemplate(str(dest), pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2.5*cm, bottomMargin=2*cm)
        story = []

        story.append(Paragraph("Sistema de Seguimiento — Estudiantes Becados", self.styles["Pie"]))
        story.append(Paragraph("Reporte General de Becados", self.styles["TituloReporte"]))
        story.append(Paragraph(
            f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            self.styles["CuerpoCentrado"],
        ))
        story.append(Spacer(1, 0.4 * cm))
        story.append(HRFlowable(width="100%", thickness=2, color=AZUL, spaceAfter=14))

        # KPIs resumen
        story.append(Paragraph("Resumen Ejecutivo", self.styles["Subtitulo"]))
        story.append(Spacer(1, 0.3 * cm))

        voluntariado_completo = sum(
            1 for ind in indicadores if ind.horas_voluntariado >= HORAS_VOLUNTARIADO_REQUERIDAS
        )
        kpi_data = [
            [
                "Becados Activos",
                "Rendimiento",
                "Asistencia Prom.",
                "Horas Voluntariado",
                "Voluntariado Completado",
            ],
            [
                str(resumen.get("total", 0)),
                f"{resumen.get('promedio_academico', 0):.2f}",
                f"{resumen.get('pct_asistencia_promedio', 0):.1f}%",
                f"{resumen.get('horas_voluntariado_promedio', 0):.1f}",
                str(voluntariado_completo),
            ],
        ]
        t = Table(kpi_data, colWidths=[3*cm, 3.2*cm, 3.2*cm, 3.2*cm, 4.4*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AZUL),
            ("TEXTCOLOR", (0, 0), (-1, 0), BLANCO),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, 1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTSIZE", (0, 1), (-1, 1), 10),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 1), (-1, 1), AZUL_CLARO),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.8 * cm))

        # Nueva sección de indicadores
        story.append(Paragraph("Indicadores", self.styles["Subtitulo"]))
        story.append(Spacer(1, 0.3 * cm))

        riesgo_bajo = resumen.get("en_riesgo_bajo", 0)
        riesgo_medio = resumen.get("en_riesgo_medio", 0)
        riesgo_alto = resumen.get("en_riesgo_alto", 0)
        total_riesgo = max(riesgo_bajo + riesgo_medio + riesgo_alto, 1)

        rendimiento = [r for r in indicadores if getattr(r, "promedio_academico", 0) > 0]
        promedio_general = round(sum(r.promedio_academico for r in rendimiento) / len(rendimiento), 2) if rendimiento else 0.0
        reprobaron = sum(1 for r in rendimiento if r.promedio_academico < 7.0)
        menor_promedio = min((r.promedio_academico for r in rendimiento), default=0.0)

        tabla_unica_data = [
            ["Riesgo Bajo", f"{riesgo_bajo} ({riesgo_bajo / total_riesgo * 100:.1f}%)", "Promedio General de Notas", f"{promedio_general:.2f}"],
            ["Riesgo Medio", f"{riesgo_medio} ({riesgo_medio / total_riesgo * 100:.1f}%)", "Becados con Materias Reprobadas", str(reprobaron)],
            ["Riesgo Alto", f"{riesgo_alto} ({riesgo_alto / total_riesgo * 100:.1f}%)", "Menor promedio registrado", f"{menor_promedio:.2f}"],
        ]
        tabla_unica = Table(
            tabla_unica_data,
            colWidths=[4.0*cm, 3.0*cm, 6.5*cm, 4*cm],
            repeatRows=0,
        )
        tabla_unica.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), AZUL),
            ("BACKGROUND", (2, 0), (2, -1), AZUL),
            ("BACKGROUND", (1, 0), (1, -1), BLANCO),
            ("BACKGROUND", (3, 0), (3, -1), BLANCO),
            ("TEXTCOLOR", (0, 0), (0, -1), BLANCO),
            ("TEXTCOLOR", (2, 0), (2, -1), BLANCO),
            ("TEXTCOLOR", (1, 0), (1, -1), NEGRO),
            ("TEXTCOLOR", (3, 0), (3, -1), NEGRO),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTNAME", (3, 0), (3, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (3, -1), 9),
            ("ALIGN", (0, 0), (3, -1), "CENTER"),
            ("VALIGN", (0, 0), (3, -1), "MIDDLE"),
            ("PADDING", (0, 0), (3, -1), 7),
            ("GRID", (0, 0), (3, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        story.append(tabla_unica)
        story.append(Spacer(1, 0.7 * cm))

        story.append(Paragraph("Voluntariado", self.styles["Subtitulo"]))
        voluntariado_data = [
            ["Horas", "Estudiantes"],
            ["0-14", str(sum(1 for ind in indicadores if 0 <= ind.horas_voluntariado <= 14))],
            ["15-29", str(sum(1 for ind in indicadores if 15 <= ind.horas_voluntariado <= 29))],
            ["30-44", str(sum(1 for ind in indicadores if 30 <= ind.horas_voluntariado <= 44))],
            ["45-60", str(sum(1 for ind in indicadores if 45 <= ind.horas_voluntariado <= 60))],
        ]
        voluntariado_table = Table(voluntariado_data, colWidths=[6*cm, 6*cm])
        voluntariado_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AZUL),
            ("TEXTCOLOR", (0, 0), (-1, 0), BLANCO),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BLANCO, GRIS_CLARO]),
        ]))
        story.append(voluntariado_table)
        story.append(Spacer(1, 0.7 * cm))

        # Tabla de todos los estudiantes
        story.append(Paragraph("Detalle por Estudiante", self.styles["Subtitulo"]))
        header = ["Nombre", "Asistencia", "Promedio", "Voluntariado", "Riesgo"]
        rows = [header]
        for ind in indicadores:
            rows.append([
                ind.nombre[:30],
                f"{ind.pct_asistencia:.1f}%",
                f"{ind.promedio_academico:.2f}",
                f"{ind.horas_voluntariado:.0f}h",
                f"{ind.nivel_riesgo}",
            ])
        col_w = [6 * cm, 3 * cm, 2.5 * cm, 3 * cm, 2.5 * cm]
        t2 = Table(rows, colWidths=col_w, repeatRows=1)
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AZUL),
            ("TEXTCOLOR", (0, 0), (-1, 0), BLANCO),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BLANCO, GRIS_CLARO]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("PADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(t2)

        story.append(Spacer(1, 1*cm))
        story.append(HRFlowable(width="100%", thickness=1, color=GRIS_CLARO, spaceAfter=6))
        story.append(Paragraph(
            "Sistema Inteligente de Seguimiento para Estudiantes Becados",
            self.styles["Pie"],
        ))

        doc.build(story)
        logger.info("Reporte general generado: %s", dest)
        return dest
