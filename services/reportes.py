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

from config import REPORTS_DIR
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
            Paragraph(f"Reporte Individual: {estudiante.nombre_completo}", self.styles["TituloReporte"]),
            Spacer(1, 0.2 * cm),
        ]

        datos = [
            ["Código", estudiante.codigo, "Estado", estudiante.estado],
            ["Monitor", estudiante.monitor, "Universidad", estudiante.universidad],
            ["Carrera", estudiante.carrera, "Ciclo", estudiante.ciclo],
        ]
        tabla_meta = Table(datos, colWidths=[3.2 * cm, 5.5 * cm, 3.2 * cm, 5.5 * cm])
        tabla_meta.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), GRIS_CLARO),
            ("TEXTCOLOR", (0, 0), (-1, -1), NEGRO),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LINEBEFORE", (1, 0), (1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("LINEBEFORE", (3, 0), (3, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("LINEABOVE", (0, 1), (-1, 1), 0.5, colors.HexColor("#E2E8F0")),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elementos.extend([
            tabla_meta,
            Spacer(1, 0.6 * cm),
        ])
        return elementos

    def _seccion_info_general(self, e: Estudiante) -> list:
        data = [
            ["Campo", "Valor", "Campo", "Valor"],
            ["Universidad", e.universidad, "Carrera", e.carrera],
            ["Ciclo", e.ciclo, "Fecha Ingreso", e.fecha_ingreso],
            ["Correo", e.correo, "Teléfono", e.telefono],
        ]
        tabla = Table(data, colWidths=[3.5 * cm, 6 * cm, 3.5 * cm, 4 * cm])
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AZUL),
            ("TEXTCOLOR", (0, 0), (-1, 0), BLANCO),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BACKGROUND", (0, 1), (-1, -1), GRIS_CLARO),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BLANCO, GRIS_CLARO]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("PADDING", (0, 0), (-1, -1), 6),
            ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 1), (2, -1), "Helvetica-Bold"),
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
             "✓ OK" if asi.get('pct_asistencia', 0) >= 75 else "✗ Bajo"],
            ["Promedio Académico", f"{ren.get('promedio', 0):.2f}",
             "✓ OK" if ren.get('promedio', 0) >= 7 else "✗ Bajo"],
            ["Horas Voluntariado", f"{vol.get('horas_acumuladas', 0):.1f} / 40h",
             "✓ Cumplido" if vol.get('cumplido', False) else "⚠ Pendiente"],
            ["Días sin seguimiento", f"{ind.dias_sin_seguimiento}",
             "✓ OK" if ind.dias_sin_seguimiento <= 30 else "⚠ Atención"],
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
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("PADDING", (0, 0), (-1, -1), 7),
        ]))
        return [
            Paragraph("Indicadores de Seguimiento", self.styles["Subtitulo"]),
            tabla,
            Spacer(1, 0.5 * cm),
        ]

    def _seccion_riesgo(self, ind: IndicadorEstudiante) -> list:
        color_nivel = _color_riesgo(ind.nivel_riesgo)
        contenido = [
            [
                Paragraph(f"<b>{ind.emoji_riesgo} {ind.nivel_riesgo}</b>", self.styles["CuerpoNormal"]),
                Paragraph(f"Índice de riesgo: <b>{ind.indice_riesgo:.2%}</b>", self.styles["CuerpoNormal"]),
            ]
        ]
        tabla_riesgo = Table(contenido, colWidths=[7.5 * cm, 5.5 * cm])
        tabla_riesgo.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), color_nivel),
            ("TEXTCOLOR", (0, 0), (-1, -1), BLANCO),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))

        elementos = [
            Paragraph("Nivel de Riesgo", self.styles["Subtitulo"]),
            tabla_riesgo,
        ]
        if ind.alertas:
            elementos.append(Spacer(1, 0.2 * cm))
            elementos.append(Paragraph("<b>Alertas activas:</b>", self.styles["CuerpoNormal"]))
            for alerta in ind.alertas:
                elementos.append(Paragraph(f"• {alerta}", self.styles["Alerta"]))
        elementos.append(Spacer(1, 0.5 * cm))
        return elementos

    def _seccion_seguimientos(self, historial: list) -> list:
        if not historial:
            return [
                Paragraph("Historial de Seguimientos", self.styles["Subtitulo"]),
                Paragraph("Sin seguimientos registrados.", self.styles["CuerpoNormal"]),
                Spacer(1, 0.5 * cm),
            ]
        data = [["Fecha", "Tipo", "Descripción", "Acción"]]
        for s in historial[:10]:  # máximo 10 en el reporte
            desc = str(s.get("Descripcion", "") or "")[:60]
            accion = str(s.get("AccionRealizada", "") or "")[:40]
            data.append([
                str(s.get("Fecha", ""))[:10],
                str(s.get("Tipo", "")),
                desc,
                accion,
            ])
        col_w = [2.5 * cm, 3.5 * cm, 6 * cm, 5 * cm]
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
            Paragraph("Historial de Seguimientos (últimos 10)", self.styles["Subtitulo"]),
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
        kpi_data = [
            ["Total Estudiantes", "En Riesgo Alto", "En Riesgo Medio", "Asistencia Promedio", "Promedio Académico"],
            [
                str(resumen.get("total", 0)),
                str(resumen.get("en_riesgo_alto", 0)),
                str(resumen.get("en_riesgo_medio", 0)),
                f"{resumen.get('pct_asistencia_promedio', 0):.1f}%",
                f"{resumen.get('promedio_academico', 0):.2f}",
            ],
        ]
        t = Table(kpi_data, colWidths=[3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AZUL),
            ("TEXTCOLOR", (0, 0), (-1, 0), BLANCO),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("FONTSIZE", (0, 1), (-1, 1), 11),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 1), (-1, 1), AZUL_CLARO),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.7*cm))

        # Distribución de riesgos
        story.append(Paragraph("Distribución de Riesgo", self.styles["Subtitulo"]))
        risk_data = [
            ["Nivel", "Cantidad", "Porcentaje"],
            ["Bajo", str(resumen.get("en_riesgo_bajo", 0)), f"{resumen.get('pct_bajo', 0):.1f}%"],
            ["Medio", str(resumen.get("en_riesgo_medio", 0)), f"{resumen.get('pct_medio', 0):.1f}%"],
            ["Alto", str(resumen.get("en_riesgo_alto", 0)), f"{resumen.get('pct_alto', 0):.1f}%"],
        ]
        r = Table(risk_data, colWidths=[5*cm, 4*cm, 5*cm])
        r.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AZUL),
            ("TEXTCOLOR", (0, 0), (-1, 0), BLANCO),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BLANCO, GRIS_CLARO]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(r)
        story.append(Spacer(1, 0.7*cm))

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
                f"{ind.emoji_riesgo} {ind.nivel_riesgo}",
            ])
        col_w = [7 * cm, 3 * cm, 3 * cm, 3 * cm, 3 * cm]
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
