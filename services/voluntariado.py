"""Servicio de gestión de voluntariado."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional

import pandas as pd

from config import SHEET_VOLUNTARIADO, HORAS_VOLUNTARIADO_REQUERIDAS
from services.excel_manager import ExcelManager
from utils.logger import logger


@dataclass
class Voluntariado:
    id: Optional[int] = None
    id_estudiante: int = 0
    actividad: str = ""
    horas: float = 0.0
    fecha: str = ""
    observacion: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ID": self.id,
            "IDEstudiante": self.id_estudiante,
            "Actividad": self.actividad,
            "Horas": self.horas,
            "Fecha": self.fecha,
            "Observacion": self.observacion,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Voluntariado":
        return cls(
            id=int(d["ID"]) if d.get("ID") else None,
            id_estudiante=int(d.get("IDEstudiante", 0) or 0),
            actividad=str(d.get("Actividad", "") or ""),
            horas=float(d.get("Horas", 0) or 0),
            fecha=str(d.get("Fecha", "") or ""),
            observacion=str(d.get("Observacion", "") or ""),
        )


class VoluntariadoService:
    """Lógica de negocio para voluntariado."""

    def __init__(self, excel: ExcelManager) -> None:
        self._excel = excel

    def registrar(self, v: Voluntariado) -> int:
        if v.horas <= 0:
            raise ValueError("Las horas deben ser mayores a 0.")
        if not v.actividad.strip():
            raise ValueError("La actividad es obligatoria.")
        if not v.fecha:
            v.fecha = datetime.now().strftime("%Y-%m-%d")
        row_id = self._excel.insert_row(SHEET_VOLUNTARIADO, v.to_dict())
        logger.info("Voluntariado registrado ID=%s", row_id)
        return row_id

    def actualizar(self, v: Voluntariado) -> bool:
        return self._excel.update_row(SHEET_VOLUNTARIADO, v.id, v.to_dict())

    def eliminar(self, voluntariado_id: int) -> bool:
        return self._excel.delete_row(SHEET_VOLUNTARIADO, voluntariado_id)

    def listar_por_estudiante(self, estudiante_id: int) -> List[Voluntariado]:
        df = self._excel.find_by_field(SHEET_VOLUNTARIADO, "IDEstudiante", estudiante_id)
        return [Voluntariado.from_dict(r) for _, r in df.iterrows()]

    def calcular_estadisticas(self, estudiante_id: int) -> Dict[str, Any]:
        registros = self.listar_por_estudiante(estudiante_id)
        horas_acumuladas = sum(r.horas for r in registros)
        horas_pendientes = max(0.0, HORAS_VOLUNTARIADO_REQUERIDAS - horas_acumuladas)
        pct = min(100.0, round(horas_acumuladas / HORAS_VOLUNTARIADO_REQUERIDAS * 100, 1))
        return {
            "total_actividades": len(registros),
            "horas_acumuladas": round(horas_acumuladas, 1),
            "horas_pendientes": round(horas_pendientes, 1),
            "horas_requeridas": HORAS_VOLUNTARIADO_REQUERIDAS,
            "pct_cumplimiento": pct,
            "cumplido": horas_acumuladas >= HORAS_VOLUNTARIADO_REQUERIDAS,
        }

    def promedio_horas_global(self) -> float:
        df = self._excel.read_sheet(SHEET_VOLUNTARIADO)
        if df.empty:
            return 0.0
        horas = pd.to_numeric(df["Horas"], errors="coerce").fillna(0)
        ids = df["IDEstudiante"].nunique()
        return round(horas.sum() / ids, 1) if ids else 0.0

    def historial_dataframe(self, estudiante_id: int) -> pd.DataFrame:
        df = self._excel.find_by_field(SHEET_VOLUNTARIADO, "IDEstudiante", estudiante_id)
        if df.empty:
            return df
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
        return df.sort_values("Fecha", ascending=False)
