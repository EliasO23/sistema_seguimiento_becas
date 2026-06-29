"""
Módulo de indicadores automáticos y cálculo de riesgo.

Implementa el algoritmo de scoring que combina asistencia,
rendimiento, voluntariado y seguimiento en un índice de riesgo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List

from config import (
    PESO_ASISTENCIA, PESO_PROMEDIO, PESO_VOLUNTARIADO, PESO_SEGUIMIENTO,
    RIESGO_BAJO_MAX, RIESGO_MEDIO_MAX,
    HORAS_VOLUNTARIADO_REQUERIDAS, PROMEDIO_MINIMO,
    PORCENTAJE_ASISTENCIA_MINIMO, DIAS_SIN_SEGUIMIENTO_ALERTA,
)
from services.asistencia import AsistenciaService
from services.voluntariado import VoluntariadoService
from services.seguimiento import SeguimientoService
from services.rendimiento import RendimientoService
from utils.logger import logger


@dataclass
class IndicadorEstudiante:
    estudiante_id: int
    nombre: str = ""
    # Sub-scores normalizados [0, 1] — 0 = peor, 1 = mejor
    score_asistencia: float = 0.0
    score_promedio: float = 0.0
    score_voluntariado: float = 0.0
    score_seguimiento: float = 0.0
    # Índice compuesto
    indice_riesgo: float = 0.0          # 0 = sin riesgo, 1 = máximo riesgo
    nivel_riesgo: str = "Bajo"          # Bajo / Medio / Alto
    emoji_riesgo: str = "🟢"
    # Alertas específicas
    alertas: List[str] = field(default_factory=list)
    # Datos crudos
    pct_asistencia: float = 0.0
    horas_voluntariado: float = 0.0
    promedio_academico: float = 0.0
    dias_sin_seguimiento: int = 0


class IndicadoresService:
    """Calcula indicadores automáticos y nivel de riesgo por estudiante."""

    def __init__(
        self,
        asistencia_svc: AsistenciaService,
        voluntariado_svc: VoluntariadoService,
        seguimiento_svc: SeguimientoService,
        rendimiento_svc: RendimientoService,
    ) -> None:
        self._asi = asistencia_svc
        self._vol = voluntariado_svc
        self._seg = seguimiento_svc
        self._ren = rendimiento_svc

    def calcular(self, estudiante_id: int, nombre: str = "") -> IndicadorEstudiante:
        """Calcula el indicador completo para un estudiante."""
        ind = IndicadorEstudiante(estudiante_id=estudiante_id, nombre=nombre)

        # ── Asistencia ────────────────────────────────────────────────────────
        asi_stats = self._asi.calcular_estadisticas(estudiante_id)
        pct_asi = asi_stats.get("pct_asistencia", 0.0)
        ind.pct_asistencia = pct_asi
        ind.score_asistencia = pct_asi / 100.0

        if pct_asi < PORCENTAJE_ASISTENCIA_MINIMO:
            ind.alertas.append(f"⚠ Asistencia baja: {pct_asi:.1f}%")

        # ── Promedio ──────────────────────────────────────────────────────────
        ren_stats = self._ren.calcular_estadisticas(estudiante_id)
        prom = ren_stats.get("promedio", 0.0)
        ind.promedio_academico = prom
        ind.score_promedio = min(prom / 10.0, 1.0)

        if prom < PROMEDIO_MINIMO and prom > 0:
            ind.alertas.append(f"⚠ Promedio bajo: {prom:.1f}")

        # ── Voluntariado ──────────────────────────────────────────────────────
        vol_stats = self._vol.calcular_estadisticas(estudiante_id)
        horas = vol_stats.get("horas_acumuladas", 0.0)
        ind.horas_voluntariado = horas
        ind.score_voluntariado = min(horas / HORAS_VOLUNTARIADO_REQUERIDAS, 1.0)

        if horas < HORAS_VOLUNTARIADO_REQUERIDAS * 0.5:
            ind.alertas.append(f"⚠ Voluntariado insuficiente: {horas:.0f}h")

        # ── Seguimiento ───────────────────────────────────────────────────────
        seg_stats = self._seg.calcular_estadisticas(estudiante_id)
        dias = seg_stats.get("dias_sin_seguimiento", 9999)
        ind.dias_sin_seguimiento = dias

        # Score: 0 días → 1.0, >90 días → 0.0
        ind.score_seguimiento = max(0.0, 1.0 - dias / 90.0)

        if dias > DIAS_SIN_SEGUIMIENTO_ALERTA:
            ind.alertas.append(f"⚠ Sin seguimiento hace {dias} días")

        # ── Índice de riesgo compuesto ────────────────────────────────────────
        # "Riesgo" = 1 - score (mayor riesgo = menor score)
        riesgo_raw = (
            (1 - ind.score_asistencia) * PESO_ASISTENCIA
            + (1 - ind.score_promedio) * PESO_PROMEDIO
            + (1 - ind.score_voluntariado) * PESO_VOLUNTARIADO
            + (1 - ind.score_seguimiento) * PESO_SEGUIMIENTO
        )
        ind.indice_riesgo = round(min(max(riesgo_raw, 0.0), 1.0), 4)

        # Clasificar nivel
        if ind.indice_riesgo <= RIESGO_BAJO_MAX:
            ind.nivel_riesgo = "Bajo"
            ind.emoji_riesgo = "🟢"
        elif ind.indice_riesgo <= RIESGO_MEDIO_MAX:
            ind.nivel_riesgo = "Medio"
            ind.emoji_riesgo = "🟡"
        else:
            ind.nivel_riesgo = "Alto"
            ind.emoji_riesgo = "🔴"

        return ind

    def calcular_lote(
        self, estudiantes: List[Dict[str, Any]]
    ) -> List[IndicadorEstudiante]:
        """Calcula indicadores para una lista de estudiantes."""
        resultados = []
        for est in estudiantes:
            try:
                eid = int(est.get("ID", 0) or 0)
                nombre = f"{est.get('Nombre', '')} {est.get('Apellido', '')}".strip()
                ind = self.calcular(eid, nombre)
                resultados.append(ind)
            except Exception as exc:
                logger.warning("Error calculando indicador para %s: %s", est, exc)
        return resultados

    def resumen_global(self, indicadores: List[IndicadorEstudiante]) -> Dict[str, Any]:
        """KPIs globales del dashboard."""
        if not indicadores:
            return {}
        total = len(indicadores)
        en_riesgo_alto = sum(1 for i in indicadores if i.nivel_riesgo == "Alto")
        en_riesgo_medio = sum(1 for i in indicadores if i.nivel_riesgo == "Medio")
        en_riesgo_bajo = sum(1 for i in indicadores if i.nivel_riesgo == "Bajo")

        pct_asi_prom = round(
            sum(i.pct_asistencia for i in indicadores) / total, 1
        )
        prom_academico = round(
            sum(i.promedio_academico for i in indicadores) / total, 2
        )
        horas_vol_prom = round(
            sum(i.horas_voluntariado for i in indicadores) / total, 1
        )
        pct_bajo = round(en_riesgo_bajo / total * 100, 1)
        pct_medio = round(en_riesgo_medio / total * 100, 1)
        pct_alto = round(en_riesgo_alto / total * 100, 1)

        return {
            "total": total,
            "en_riesgo_alto": en_riesgo_alto,
            "en_riesgo_medio": en_riesgo_medio,
            "en_riesgo_bajo": en_riesgo_bajo,
            "pct_bajo": pct_bajo,
            "pct_medio": pct_medio,
            "pct_alto": pct_alto,
            "pct_asistencia_promedio": pct_asi_prom,
            "promedio_academico": prom_academico,
            "horas_voluntariado_promedio": horas_vol_prom,
        }

    def top_estudiantes(
        self, indicadores: List[IndicadorEstudiante], n: int = 5
    ) -> List[IndicadorEstudiante]:
        """Retorna los n estudiantes con menor índice de riesgo (mejores)."""
        return sorted(indicadores, key=lambda x: x.indice_riesgo)[:n]

    def estudiantes_en_riesgo(
        self, indicadores: List[IndicadorEstudiante]
    ) -> List[IndicadorEstudiante]:
        """Retorna solo estudiantes en riesgo medio o alto."""
        return [i for i in indicadores if i.nivel_riesgo in ("Medio", "Alto")]
