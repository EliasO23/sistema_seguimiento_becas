"""Servicio de rendimiento académico."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional

import pandas as pd

from config import SHEET_RENDIMIENTO, PROMEDIO_MINIMO
from services.excel_manager import ExcelManager
from utils.logger import logger


@dataclass
class Rendimiento:
    id: Optional[int] = None
    id_estudiante: int = 0
    ciclo: str = ""
    promedio: float = 0.0
    materias_aprobadas: int = 0
    materias_reprobadas: int = 0
    materias_en_riesgo: int = 0
    fecha_actualizacion: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ID": self.id,
            "IDEstudiante": self.id_estudiante,
            "Ciclo": self.ciclo,
            "Promedio": self.promedio,
            "MateriasAprobadas": self.materias_aprobadas,
            "MateriasReprobadas": self.materias_reprobadas,
            "MateriasEnRiesgo": self.materias_en_riesgo,
            "FechaActualizacion": self.fecha_actualizacion,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Rendimiento":
        return cls(
            id=int(d["ID"]) if d.get("ID") else None,
            id_estudiante=int(d.get("IDEstudiante", 0) or 0),
            ciclo=str(d.get("Ciclo", "") or ""),
            promedio=float(d.get("Promedio", 0) or 0),
            materias_aprobadas=int(d.get("MateriasAprobadas", 0) or 0),
            materias_reprobadas=int(d.get("MateriasReprobadas", 0) or 0),
            materias_en_riesgo=int(d.get("MateriasEnRiesgo", 0) or 0),
            fecha_actualizacion=str(d.get("FechaActualizacion", "") or ""),
        )


class RendimientoService:
    """Lógica de negocio para rendimiento académico."""

    def __init__(self, excel: ExcelManager) -> None:
        self._excel = excel

    def registrar(self, r: Rendimiento) -> int:
        if not 0 <= r.promedio <= 10:
            raise ValueError("El promedio debe estar entre 0 y 10.")
        if not r.fecha_actualizacion:
            r.fecha_actualizacion = datetime.now().strftime("%Y-%m-%d")
        row_id = self._excel.insert_row(SHEET_RENDIMIENTO, r.to_dict())
        logger.info("Rendimiento registrado ID=%s", row_id)
        return row_id

    def actualizar(self, r: Rendimiento) -> bool:
        return self._excel.update_row(SHEET_RENDIMIENTO, r.id, r.to_dict())

    def eliminar(self, rend_id: int) -> bool:
        return self._excel.delete_row(SHEET_RENDIMIENTO, rend_id)

    def obtener_por_id(self, rend_id: int) -> Optional[Rendimiento]:
        data = self._excel.find_by_id(SHEET_RENDIMIENTO, rend_id)
        return Rendimiento.from_dict(data) if data else None

    def listar_todos(self) -> List[Rendimiento]:
        df = self._excel.read_sheet(SHEET_RENDIMIENTO)
        return [Rendimiento.from_dict(r) for _, r in df.iterrows()]

    def obtener_por_estudiante(self, estudiante_id: int) -> Optional[Rendimiento]:
        """Retorna el registro más reciente de rendimiento."""
        df = self._excel.find_by_field(SHEET_RENDIMIENTO, "IDEstudiante", estudiante_id)
        if df.empty:
            return None
        df["FechaActualizacion"] = pd.to_datetime(df["FechaActualizacion"], errors="coerce")
        ultimo = df.sort_values("FechaActualizacion", ascending=False).iloc[0]
        return Rendimiento.from_dict(ultimo.to_dict())

    def historial_por_estudiante(self, estudiante_id: int) -> List[Rendimiento]:
        df = self._excel.find_by_field(SHEET_RENDIMIENTO, "IDEstudiante", estudiante_id)
        return [Rendimiento.from_dict(r) for _, r in df.iterrows()]

    def calcular_estadisticas(self, estudiante_id: int) -> Dict[str, Any]:
        r = self.obtener_por_estudiante(estudiante_id)
        if not r:
            return {
                "promedio": 0.0,
                "materias_aprobadas": 0,
                "materias_reprobadas": 0,
                "materias_en_riesgo": 0,
                "bajo_minimo": True,
                "fecha_actualizacion": "—",
            }
        return {
            "promedio": r.promedio,
            "materias_aprobadas": r.materias_aprobadas,
            "materias_reprobadas": r.materias_reprobadas,
            "materias_en_riesgo": r.materias_en_riesgo,
            "bajo_minimo": r.promedio < PROMEDIO_MINIMO,
            "fecha_actualizacion": r.fecha_actualizacion,
        }

    def promedio_global(self, estudiante_ids: Optional[List[int]] = None) -> float:
        df = self._excel.read_sheet(SHEET_RENDIMIENTO)
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
        promedios = pd.to_numeric(df["Promedio"], errors="coerce").dropna()
        return round(promedios.mean(), 2) if not promedios.empty else 0.0
