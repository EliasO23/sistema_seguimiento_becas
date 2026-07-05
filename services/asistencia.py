"""Servicio de gestión de asistencias."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
from typing import Dict, Any, List, Optional

import pandas as pd

from config import SHEET_ASISTENCIAS, ESTADOS_ASISTENCIA
from services.excel_manager import ExcelManager
from utils.logger import logger


@dataclass
class Asistencia:
    id: Optional[int] = None
    id_estudiante: int = 0
    fecha: str = ""
    estado: str = "Presente"
    observacion: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ID": self.id,
            "IDEstudiante": self.id_estudiante,
            "Fecha": self.fecha,
            "Estado": self.estado,
            "Observacion": self.observacion,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Asistencia":
        return cls(
            id=int(d["ID"]) if d.get("ID") else None,
            id_estudiante=int(d.get("IDEstudiante", 0) or 0),
            fecha=str(d.get("Fecha", "") or ""),
            estado=str(d.get("Estado", "Presente") or "Presente"),
            observacion=str(d.get("Observacion", "") or ""),
        )


class AsistenciaService:
    """Lógica de negocio para asistencias."""

    def __init__(self, excel: ExcelManager) -> None:
        self._excel = excel

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def registrar(self, asistencia: Asistencia) -> int:
        if asistencia.estado not in ESTADOS_ASISTENCIA:
            raise ValueError(f"Estado inválido: {asistencia.estado}")
        if not asistencia.fecha:
            asistencia.fecha = datetime.now().strftime("%Y-%m-%d")
        row_id = self._excel.insert_row(SHEET_ASISTENCIAS, asistencia.to_dict())
        logger.info("Asistencia registrada ID=%s", row_id)
        return row_id

    def actualizar(self, asistencia: Asistencia) -> bool:
        return self._excel.update_row(SHEET_ASISTENCIAS, asistencia.id, asistencia.to_dict())

    def eliminar(self, asistencia_id: int) -> bool:
        return self._excel.delete_row(SHEET_ASISTENCIAS, asistencia_id)

    def listar_por_estudiante(self, estudiante_id: int) -> List[Asistencia]:
        df = self._excel.find_by_field(SHEET_ASISTENCIAS, "IDEstudiante", estudiante_id)
        return [Asistencia.from_dict(r) for _, r in df.iterrows()]

    def obtener_todas(self) -> pd.DataFrame:
        return self._excel.read_sheet(SHEET_ASISTENCIAS)

    def resumen_por_estudiante(self, df: Optional[pd.DataFrame] = None, mes: Optional[str] = None) -> List[Dict[str, Any]]:
        """Agrupa las asistencias por estudiante con conteos y porcentaje de presencia."""
        source = df if df is not None else self._excel.read_sheet(SHEET_ASISTENCIAS)
        if source is None or source.empty:
            return []

        data = source.copy()
        if "IDEstudiante" not in data.columns or "Estado" not in data.columns:
            return []

        data = data.where(pd.notna(data), None)
        data["IDEstudiante"] = data["IDEstudiante"].astype(str).replace({"nan": "", "None": ""})
        data["Estado"] = data["Estado"].astype(str).replace({"nan": "", "None": ""})

        if mes and "Fecha" in data.columns:
            data = data[data["Fecha"].astype(str).str.startswith(str(mes), na=False)].copy()

        rows: List[Dict[str, Any]] = []
        for estudiante_id, group in data.groupby("IDEstudiante", dropna=False):
            if not str(estudiante_id).strip():
                continue
            total = len(group)
            presentes = int((group["Estado"] == "Presente").sum())
            ausentes = int((group["Estado"] == "Ausente").sum())
            tardanzas = int((group["Estado"] == "Tardanza").sum())
            justificados = int((group["Estado"] == "Justificado").sum())
            pct = round((presentes / total) * 100, 1) if total else 0.0
            rows.append({
                "id": str(estudiante_id),
                "total": total,
                "presentes": presentes,
                "ausentes": ausentes,
                "tardanzas": tardanzas,
                "justificados": justificados,
                "pct_asistencia": pct,
            })

        return sorted(rows, key=lambda r: (int(r["id"]) if str(r["id"]).isdigit() else 10**9, r["total"]), reverse=False)

    def meses_disponibles(self, df: Optional[pd.DataFrame] = None) -> List[str]:
        """Retorna los meses disponibles en formato YYYY-MM ordenados ascendentemente."""
        source = df if df is not None else self._excel.read_sheet(SHEET_ASISTENCIAS)
        if source is None or source.empty or "Fecha" not in source.columns:
            return []

        fechas = source["Fecha"].dropna().astype(str)
        meses = set()
        for fecha in fechas:
            text = fecha.strip()
            if not text:
                continue
            try:
                parsed = pd.to_datetime(text, errors="coerce")
            except Exception:
                continue
            if pd.notna(parsed):
                meses.add(parsed.strftime("%Y-%m"))

        return sorted(meses)

    # ── Cálculos ──────────────────────────────────────────────────────────────

    def calcular_estadisticas(self, estudiante_id: int) -> Dict[str, Any]:
        """Calcula métricas de asistencia para un estudiante."""
        registros = self.listar_por_estudiante(estudiante_id)
        total = len(registros)
        if total == 0:
            return {
                "total": 0,
                "presentes": 0,
                "ausentes": 0,
                "tardanzas": 0,
                "justificados": 0,
                "pct_asistencia": 0.0,
                "pct_inasistencia": 0.0,
                "dias_consecutivos_ausente": 0,
            }

        presentes = sum(1 for r in registros if r.estado == "Presente")
        ausentes = sum(1 for r in registros if r.estado == "Ausente")
        tardanzas = sum(1 for r in registros if r.estado == "Tardanza")
        justificados = sum(1 for r in registros if r.estado == "Justificado")

        asistidos = presentes + tardanzas + justificados
        pct = round(asistidos / total * 100, 2) if total else 0.0

        # Días consecutivos ausente (desde el último registro)
        fechas_ausentes = self._dias_consecutivos(registros)

        return {
            "total": total,
            "presentes": presentes,
            "ausentes": ausentes,
            "tardanzas": tardanzas,
            "justificados": justificados,
            "pct_asistencia": pct,
            "pct_inasistencia": round(100 - pct, 2),
            "dias_consecutivos_ausente": fechas_ausentes,
        }

    @staticmethod
    def _dias_consecutivos(registros: List[Asistencia]) -> int:
        """Calcula cuántos días consecutivos lleva ausente desde el más reciente."""
        sorted_recs = sorted(
            registros,
            key=lambda r: r.fecha or "",
            reverse=True,
        )
        count = 0
        for r in sorted_recs:
            if r.estado == "Ausente":
                count += 1
            else:
                break
        return count

    def historial_dataframe(self, estudiante_id: int) -> pd.DataFrame:
        df = self._excel.find_by_field(SHEET_ASISTENCIAS, "IDEstudiante", estudiante_id)
        if df.empty:
            return df
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
        return df.sort_values("Fecha", ascending=False)

    def asistencia_por_mes(self, estudiante_id: int) -> pd.DataFrame:
        """Agrupa asistencias por mes para gráficos de línea."""
        df = self.historial_dataframe(estudiante_id)
        if df.empty:
            return pd.DataFrame()
        df["Mes"] = df["Fecha"].dt.to_period("M").astype(str)
        resumen = df.groupby(["Mes", "Estado"]).size().unstack(fill_value=0)
        return resumen

    def promedio_asistencia_global(self, estudiante_ids: Optional[List[int]] = None) -> float:
        """Porcentaje promedio de asistencia de los estudiantes indicados."""
        df = self._excel.read_sheet(SHEET_ASISTENCIAS)
        if df.empty:
            return 0.0
        if estudiante_ids:
            ids = {str(i) for i in estudiante_ids if i}
            if "IDEstudiante" in df.columns:
                df = df[df["IDEstudiante"].astype(str).isin(ids)]
            else:
                return 0.0
        if df.empty:
            return 0.0
        total = len(df)
        asistidos = df[df["Estado"].isin(["Presente", "Tardanza", "Justificado"])].shape[0]
        return round(asistidos / total * 100, 1) if total else 0.0
