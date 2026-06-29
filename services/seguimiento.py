"""Servicio de gestión de seguimientos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional

import pandas as pd

from config import SHEET_SEGUIMIENTOS, TIPOS_SEGUIMIENTO, DIAS_SIN_SEGUIMIENTO_ALERTA
from services.excel_manager import ExcelManager
from utils.logger import logger


@dataclass
class Seguimiento:
    id: Optional[int] = None
    id_estudiante: int = 0
    fecha: str = ""
    tipo: str = ""
    descripcion: str = ""
    accion_realizada: str = ""
    proximo_seguimiento: str = ""
    observaciones: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ID": self.id,
            "IDEstudiante": self.id_estudiante,
            "Fecha": self.fecha,
            "Tipo": self.tipo,
            "Descripcion": self.descripcion,
            "AccionRealizada": self.accion_realizada,
            "ProximoSeguimiento": self.proximo_seguimiento,
            "Observaciones": self.observaciones,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Seguimiento":
        return cls(
            id=int(d["ID"]) if d.get("ID") else None,
            id_estudiante=int(d.get("IDEstudiante", 0) or 0),
            fecha=str(d.get("Fecha", "") or ""),
            tipo=str(d.get("Tipo", "") or ""),
            descripcion=str(d.get("Descripcion", "") or ""),
            accion_realizada=str(d.get("AccionRealizada", "") or ""),
            proximo_seguimiento=str(d.get("ProximoSeguimiento", "") or ""),
            observaciones=str(d.get("Observaciones", "") or ""),
        )


class SeguimientoService:
    """Lógica de negocio para seguimientos."""

    def __init__(self, excel: ExcelManager) -> None:
        self._excel = excel

    def registrar(self, s: Seguimiento) -> int:
        if not s.descripcion.strip():
            raise ValueError("La descripción es obligatoria.")
        if s.tipo not in TIPOS_SEGUIMIENTO:
            raise ValueError(f"Tipo de seguimiento inválido: {s.tipo}")
        if not s.fecha:
            s.fecha = datetime.now().strftime("%Y-%m-%d")
        row_id = self._excel.insert_row(SHEET_SEGUIMIENTOS, s.to_dict())
        logger.info("Seguimiento registrado ID=%s", row_id)
        return row_id

    def actualizar(self, s: Seguimiento) -> bool:
        return self._excel.update_row(SHEET_SEGUIMIENTOS, s.id, s.to_dict())

    def eliminar(self, seg_id: int) -> bool:
        return self._excel.delete_row(SHEET_SEGUIMIENTOS, seg_id)

    def listar_por_estudiante(self, estudiante_id: int) -> List[Seguimiento]:
        df = self._excel.find_by_field(SHEET_SEGUIMIENTOS, "IDEstudiante", estudiante_id)
        return [Seguimiento.from_dict(r) for _, r in df.iterrows()]

    def calcular_estadisticas(self, estudiante_id: int) -> Dict[str, Any]:
        registros = self.listar_por_estudiante(estudiante_id)
        total = len(registros)
        dias_sin_seg = self._dias_sin_seguimiento(registros)
        return {
            "total": total,
            "dias_sin_seguimiento": dias_sin_seg,
            "alerta_seguimiento": dias_sin_seg > DIAS_SIN_SEGUIMIENTO_ALERTA,
            "ultimo_tipo": registros[-1].tipo if registros else "—",
            "ultimo_fecha": registros[-1].fecha if registros else "—",
        }

    @staticmethod
    def _dias_sin_seguimiento(registros: List[Seguimiento]) -> int:
        if not registros:
            return 9999  # nunca se ha hecho seguimiento
        fechas = []
        for r in registros:
            try:
                fechas.append(datetime.strptime(r.fecha[:10], "%Y-%m-%d"))
            except (ValueError, TypeError):
                pass
        if not fechas:
            return 9999
        ultimo = max(fechas)
        return (datetime.now() - ultimo).days

    def historial_dataframe(self, estudiante_id: int) -> pd.DataFrame:
        df = self._excel.find_by_field(SHEET_SEGUIMIENTOS, "IDEstudiante", estudiante_id)
        if df.empty:
            return df
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
        return df.sort_values("Fecha", ascending=False)

    def proximos_seguimientos(self) -> pd.DataFrame:
        """Retorna seguimientos con próxima fecha en los próximos 7 días."""
        df = self._excel.read_sheet(SHEET_SEGUIMIENTOS)
        if df.empty or "ProximoSeguimiento" not in df.columns:
            return pd.DataFrame()
        df["ProximoSeguimiento"] = pd.to_datetime(df["ProximoSeguimiento"], errors="coerce")
        hoy = datetime.now()
        limite = hoy + timedelta(days=7)
        return df[(df["ProximoSeguimiento"] >= hoy) & (df["ProximoSeguimiento"] <= limite)]

    def total_seguimientos_global(self) -> int:
        df = self._excel.read_sheet(SHEET_SEGUIMIENTOS)
        return len(df)
