# 🎓 Sistema Inteligente de Seguimiento para Estudiantes Becados

Sistema de escritorio desarrollado completamente en Python que automatiza el seguimiento de estudiantes becados universitarios, transformando datos en indicadores accionables.

---

## ✨ Características principales

| Módulo | Descripción |
|--------|-------------|
| 🏠 **Dashboard** | KPIs en tiempo real, gráficos integrados, alertas automáticas |
| 👥 **Estudiantes** | CRUD completo, búsqueda, filtros, foto de perfil |
| 📋 **Seguimiento** | Registro de conversaciones, compromisos y próximas citas |
| ✅ **Asistencia** | Control diario, estadísticas, días consecutivos ausente |
| 🤝 **Voluntariado** | Registro de horas, cumplimiento de meta (40h) |
| 📊 **Reportes** | PDF profesionales, export a Excel y CSV |
| 🔴 **Riesgo** | Algoritmo automático con 4 indicadores ponderados |
| 👁 **Perfil** | Ficha completa con gráfico radar y asistencia mensual |

---

## 🛠 Tecnologías

- **Python 3.12+**
- **CustomTkinter** — Interfaz moderna estilo Notion/PowerBI
- **Pandas + NumPy** — Análisis de datos
- **OpenPyXL** — Gestión del Excel como base de datos
- **Matplotlib** — Gráficos integrados (no ventanas externas)
- **ReportLab** — Generación de PDFs profesionales

---

## 🚀 Instalación y ejecución

### 1. Clonar o descomprimir el proyecto

```bash
cd SistemaBecas
```

### 2. Crear entorno virtual (recomendado)

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / Mac
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Ejecutar

```bash
python main.py
```

Al iniciar por primera vez, el sistema generará automáticamente **100 estudiantes de prueba** con asistencias, seguimientos, voluntariado y rendimiento académico.

---

## 📁 Estructura del proyecto

```
SistemaBecas/
├── main.py                  # Punto de entrada con splash screen
├── config.py                # Configuración global y constantes
├── requirements.txt
├── README.md
│
├── data/
│   ├── becados.xlsx         # Base de datos Excel (auto-generada)
│   ├── backups/             # Copias de seguridad automáticas
│   └── generar_datos.py     # Generador de datos de prueba
│
├── services/                # Capa de negocio (sin acceso directo a UI)
│   ├── excel_manager.py     # Único punto de acceso al Excel
│   ├── estudiantes.py
│   ├── asistencia.py
│   ├── voluntariado.py
│   ├── seguimiento.py
│   ├── rendimiento.py
│   ├── indicadores.py       # Algoritmo de riesgo
│   └── reportes.py          # Generación PDF
│
├── ui/                      # Capa de presentación
│   ├── app.py               # Ventana principal
│   ├── menu.py              # Sidebar de navegación
│   ├── dashboard.py
│   ├── estudiantes.py
│   ├── seguimiento.py
│   ├── asistencia.py
│   ├── voluntariado.py
│   ├── perfil.py            # Ficha completa del estudiante
│   ├── reportes_view.py
│   ├── config_view.py
│   └── components/
│       └── cards.py         # Componentes reutilizables
│
├── utils/
│   └── logger.py
│
├── reports/                 # PDFs generados
└── exports/                 # CSV/Excel exportados
```

---

## 📊 Algoritmo de Riesgo

El sistema calcula automáticamente un **índice de riesgo** para cada estudiante combinando 4 dimensiones:

| Dimensión | Peso | Descripción |
|-----------|------|-------------|
| Asistencia | 40% | Porcentaje de días asistidos |
| Promedio académico | 30% | Calificación sobre 10 |
| Voluntariado | 20% | Horas completadas / 40h meta |
| Seguimiento | 10% | Tiempo desde el último contacto |

**Clasificación:**
- 🟢 **Bajo** — Índice ≤ 40%
- 🟡 **Medio** — Índice entre 40% y 70%
- 🔴 **Alto** — Índice > 70%

---

## 🗄 Estructura del Excel (becados.xlsx)

El archivo funciona como base de datos con 6 hojas:

1. **Estudiantes** — Datos personales y académicos
2. **Asistencias** — Registro diario de asistencia
3. **Voluntariado** — Actividades y horas
4. **Seguimientos** — Historial de conversaciones del monitor
5. **Rendimiento** — Promedios y materias por ciclo
6. **Configuracion** — Parámetros del sistema

---

## 📄 Reportes disponibles

- **Reporte individual**: Perfil completo con indicadores, alertas y recomendaciones automáticas
- **Reporte general**: Consolidado de todos los estudiantes con KPIs globales
- **Reporte de riesgo**: Solo estudiantes en riesgo medio/alto

---

## 🔒 Buenas prácticas implementadas

- Arquitectura en capas (UI ↔ Services ↔ Excel)
- Principios SOLID
- Type Hints completos
- Logging de eventos y errores
- Backups automáticos antes de escrituras críticas
- Caché de lectura para rendimiento
- Threading para operaciones pesadas (UI no se congela)
- Validaciones robustas en cada servicio

---

## 📝 Notas de uso

- El archivo `becados.xlsx` se genera automáticamente en `data/`.
- Los reportes PDF se guardan en `reports/`.
- Las exportaciones se guardan en `exports/`.
- Los logs se guardan en `sistema_becas.log`.
