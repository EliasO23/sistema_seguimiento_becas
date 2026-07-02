"""Servicio de gestión de estudiantes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

import pandas as pd

from config import SHEET_ESTUDIANTES, ESTADOS_ESTUDIANTE
from services.excel_manager import ExcelManager
from utils.logger import logger


@dataclass
class Estudiante:
    id: Optional[int] = None
    codigo: str = ""
    nombre: str = ""
    apellido: str = ""
    universidad: str = ""
    carrera: str = ""
    ciclo: str = ""
    correo: str = ""
    telefono: str = ""
    fecha_ingreso: str = ""
    monitor: str = ""
    estado: str = "Activo"
    fotografia: str = ""

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}".strip()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ID": self.id,
            "Codigo": self.codigo,
            "Nombre": self.nombre,
            "Apellido": self.apellido,
            "Universidad": self.universidad,
            "Carrera": self.carrera,
            "Ciclo": self.ciclo,
            "Correo": self.correo,
            "Telefono": self.telefono,
            "FechaIngreso": self.fecha_ingreso,
            "Monitor": self.monitor,
            "Estado": self.estado,
            "Fotografia": self.fotografia,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Estudiante":
        estado = str(d.get("Estado", "Activo") or "Activo")
        return cls(
            id=int(d.get("ID", 0)) if d.get("ID") else None,
            codigo=str(d.get("Codigo", "") or ""),
            nombre=str(d.get("Nombre", "") or ""),
            apellido=str(d.get("Apellido", "") or ""),
            universidad=str(d.get("Universidad", "") or ""),
            carrera=str(d.get("Carrera", "") or ""),
            ciclo=str(d.get("Ciclo", "") or ""),
            correo=str(d.get("Correo", "") or ""),
            telefono=str(d.get("Telefono", "") or ""),
            fecha_ingreso=str(d.get("FechaIngreso", "") or ""),
            monitor=str(d.get("Monitor", "") or ""),
            estado=cls._normalizar_estado(estado),
            fotografia=str(d.get("Fotografia", "") or ""),
        )

    @staticmethod
    def _normalizar_estado(estado: str) -> str:
        estado = (estado or "").strip()
        if estado in {"Inactivo", "Egresado", "Retirado"}:
            return "Retirado"
        if estado in {"Activo", "Suspendido"}:
            return estado
        return estado


class EstudiantesService:
    """Lógica de negocio para la gestión de estudiantes."""

    def __init__(self, excel: ExcelManager) -> None:
        self._excel = excel

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def crear(self, estudiante: Estudiante) -> int:
        """Registra un nuevo estudiante y retorna su ID."""
        self._validar(estudiante)
        row_id = self._excel.insert_row(SHEET_ESTUDIANTES, estudiante.to_dict())
        logger.info("Estudiante creado: %s (ID=%s)", estudiante.nombre_completo, row_id)
        return row_id

    def actualizar(self, estudiante: Estudiante) -> bool:
        """Actualiza los datos de un estudiante existente."""
        if not estudiante.id:
            raise ValueError("El estudiante no tiene ID asignado.")
        self._validar(estudiante)
        ok = self._excel.update_row(SHEET_ESTUDIANTES, estudiante.id, estudiante.to_dict())
        if ok:
            logger.info("Estudiante actualizado ID=%s", estudiante.id)
        return ok

    def eliminar(self, estudiante_id: int) -> bool:
        """Elimina un estudiante por ID."""
        ok = self._excel.delete_row(SHEET_ESTUDIANTES, estudiante_id)
        if ok:
            logger.info("Estudiante eliminado ID=%s", estudiante_id)
        return ok

    def obtener_por_id(self, estudiante_id: int) -> Optional[Estudiante]:
        """Retorna un estudiante por su ID."""
        data = self._excel.find_by_id(SHEET_ESTUDIANTES, estudiante_id)
        return Estudiante.from_dict(data) if data else None

    def listar_todos(self) -> List[Estudiante]:
        """Retorna todos los estudiantes."""
        df = self._excel.read_sheet(SHEET_ESTUDIANTES)
        return [Estudiante.from_dict(row) for _, row in df.iterrows()]

    def listar_activos(self) -> List[Estudiante]:
        """Retorna solo estudiantes activos."""
        return [e for e in self.listar_todos() if e.estado == "Activo"]

    def buscar(self, query: str) -> List[Estudiante]:
        """Búsqueda de texto libre."""
        df = self._excel.search(SHEET_ESTUDIANTES, query)
        return [Estudiante.from_dict(row) for _, row in df.iterrows()]

    def filtrar_por_estado(self, estado: str) -> List[Estudiante]:
        df = self._excel.find_by_field(SHEET_ESTUDIANTES, "Estado", estado)
        return [Estudiante.from_dict(row) for _, row in df.iterrows()]

    def filtrar_por_universidad(self, universidad: str) -> List[Estudiante]:
        df = self._excel.find_by_field(SHEET_ESTUDIANTES, "Universidad", universidad)
        return [Estudiante.from_dict(row) for _, row in df.iterrows()]

    # ── DataFrame para tablas UI ──────────────────────────────────────────────

    def dataframe(self) -> pd.DataFrame:
        return self._excel.read_sheet(SHEET_ESTUDIANTES)

    # ── Validaciones ──────────────────────────────────────────────────────────

    @staticmethod
    def _validar(e: Estudiante) -> None:
        if not e.nombre.strip():
            raise ValueError("El nombre es obligatorio.")
        if not e.apellido.strip():
            raise ValueError("El apellido es obligatorio.")
        if e.estado not in ESTADOS_ESTUDIANTE:
            raise ValueError(f"Estado inválido: {e.estado}")
        if e.correo and "@" not in e.correo:
            raise ValueError("Correo electrónico inválido.")

    # ── Estadísticas ──────────────────────────────────────────────────────────

    def estadisticas_generales(self) -> Dict[str, Any]:
        todos = self.listar_todos()
        por_estado = {}
        for e in todos:
            por_estado[e.estado] = por_estado.get(e.estado, 0) + 1
        return {
            "total": len(todos),
            "activos": por_estado.get("Activo", 0),
            "retirados": por_estado.get("Retirado", 0),
            "suspendidos": por_estado.get("Suspendido", 0),
            "por_estado": por_estado,
        }
