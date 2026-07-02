"""
Sistema Inteligente de Seguimiento para Estudiantes Becados
Configuración global del sistema.
"""

from pathlib import Path
from typing import Dict, Any

# ── Importar carreras y universidades ────────────────────────────────────────
from data.carreras_universidades import universidades as _universidades_dict

# ── Rutas base ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
EXPORTS_DIR = BASE_DIR / "exports"
IMAGES_DIR = BASE_DIR / "images"
ASSETS_DIR = BASE_DIR / "assets"
UTILS_DIR = BASE_DIR / "utils"
TEMPLATES_DIR = DATA_DIR / "plantillas"
BACKUPS_DIR = DATA_DIR / "backups"

# Crear directorios si no existen
for _dir in [DATA_DIR, REPORTS_DIR, EXPORTS_DIR, IMAGES_DIR,
             ASSETS_DIR, TEMPLATES_DIR, BACKUPS_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)

# ── Archivo principal ────────────────────────────────────────────────────────
EXCEL_FILE = DATA_DIR / "becados.xlsx"

# ── Hojas del Excel ──────────────────────────────────────────────────────────
SHEET_ESTUDIANTES = "Estudiantes"
SHEET_ASISTENCIAS = "Asistencias"
SHEET_VOLUNTARIADO = "Voluntariado"
SHEET_SEGUIMIENTOS = "Seguimientos"
SHEET_RENDIMIENTO = "Rendimiento"
SHEET_CONFIG = "Configuracion"

ALL_SHEETS = [
    SHEET_ESTUDIANTES,
    SHEET_ASISTENCIAS,
    SHEET_VOLUNTARIADO,
    SHEET_SEGUIMIENTOS,
    SHEET_RENDIMIENTO,
    SHEET_CONFIG,
]

# ── Columnas por hoja ────────────────────────────────────────────────────────
COLS_ESTUDIANTES = [
    "ID", "Codigo", "Nombre", "Apellido", "Universidad",
    "Carrera", "Ciclo", "Correo", "Telefono",
    "FechaIngreso", "Monitor", "Estado", "Fotografia",
]

COLS_ASISTENCIAS = [
    "ID", "IDEstudiante", "Fecha", "Estado", "Observacion",
]

COLS_VOLUNTARIADO = [
    "ID", "IDEstudiante", "Actividad", "Horas", "Fecha", "Observacion",
]

COLS_SEGUIMIENTOS = [
    "ID", "IDEstudiante", "Fecha", "Tipo", "Descripcion",
    "AccionRealizada", "ProximoSeguimiento", "Observaciones",
]

COLS_RENDIMIENTO = [
    "ID", "IDEstudiante", "Promedio", "MateriasAprobadas",
    "MateriasReprobadas", "MateriasEnRiesgo", "FechaActualizacion",
]

COLS_CONFIG = ["Clave", "Valor", "Descripcion"]

# ── Parámetros de negocio ─────────────────────────────────────────────────────
HORAS_VOLUNTARIADO_REQUERIDAS: float = 60.0
PROMEDIO_MINIMO: float = 7.0
PORCENTAJE_ASISTENCIA_MINIMO: float = 75.0
DIAS_SIN_SEGUIMIENTO_ALERTA: int = 30

# Pesos del índice de riesgo (deben sumar 1.0)
PESO_ASISTENCIA: float = 0.40
PESO_PROMEDIO: float = 0.30
PESO_VOLUNTARIADO: float = 0.20
PESO_SEGUIMIENTO: float = 0.10

# Umbrales de riesgo
RIESGO_BAJO_MAX: float = 0.40
RIESGO_MEDIO_MAX: float = 0.70

# ── Paleta de colores ────────────────────────────────────────────────────────
COLORS: Dict[str, str] = {
    # Primarios
    "primary": "#2563EB",
    "primary_dark": "#1D4ED8",
    "primary_light": "#DBEAFE",
    # Fondos
    "bg_main": "#F8FAFC",
    "bg_card": "#FFFFFF",
    "bg_sidebar": "#1E293B",
    "bg_sidebar_hover": "#334155",
    # Texto
    "text_primary": "#0F172A",
    "text_secondary": "#64748B",
    "text_light": "#94A3B8",
    "text_white": "#FFFFFF",
    # Estado
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "info": "#3B82F6",
    # Riesgo
    "riesgo_bajo": "#10B981",
    "riesgo_medio": "#F59E0B",
    "riesgo_alto": "#EF4444",
    # Bordes
    "border": "#E2E8F0",
    "border_focus": "#2563EB",
}

# ── Tipografía ───────────────────────────────────────────────────────────────
FONTS: Dict[str, Any] = {
    "heading_xl": ("Segoe UI", 28, "bold"),
    "heading_lg": ("Segoe UI", 20, "bold"),
    "heading_md": ("Segoe UI", 16, "bold"),
    "heading_sm": ("Segoe UI", 13, "bold"),
    "body": ("Segoe UI", 12),
    "body_sm": ("Segoe UI", 11),
    "caption": ("Segoe UI", 10),
    "mono": ("Consolas", 11),
}

# ── Dimensiones de ventana ───────────────────────────────────────────────────
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 780
SIDEBAR_WIDTH = 220
TABLE_RENDER_LIMIT = 250

# Máximo ancho para contenedores centrados en la UI (responsivo)
CONTENT_MAX_WIDTH = 980

# ── Logging ──────────────────────────────────────────────────────────────────
LOG_FILE = BASE_DIR / "sistema_becas.log"
LOG_LEVEL = "INFO"

# ── Universidades y carreras de ejemplo ─────────────────────────────────────
# Importadas desde data/carreras_universidades.py
UNIVERSIDADES = list(_universidades_dict.keys())

# Extraer todas las carreras únicas de todas las universidades
_carreras_set = set()
for carreras in _universidades_dict.values():
    _carreras_set.update(carreras)
CARRERAS = sorted(list(_carreras_set))

TIPOS_SEGUIMIENTO = [
    "Reunión presencial",
    "Llamada telefónica",
    "Correo electrónico",
    "WhatsApp",
    "Videollamada",
    "Visita domiciliar",
]

ESTADOS_ASISTENCIA = ["Presente", "Ausente", "Tardanza", "Justificado"]
ESTADOS_ESTUDIANTE = ["Activo", "Retirado", "Suspendido"]
