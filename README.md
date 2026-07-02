# 🎓 Sistema Inteligente de Seguimiento para Estudiantes Becados

Sistema de escritorio desarrollado en Python que automatiza el seguimiento de estudiantes becados universitarios mediante un Excel como base de datos y una UI moderna con CustomTkinter.

---

## ✨ Características principales

| Módulo | Descripción |
|--------|-------------|
| 🏠 **Dashboard** | KPIs globales, gráficos de riesgo y resumen de desempeño |
| 👥 **Estudiantes** | Gestión completa de estudiantes con búsqueda, filtros y perfil |
| 📋 **Seguimiento** | Registro de contactos, acciones realizadas y próximas citas |
| ✅ **Asistencia** | Control diario de asistencias con estadísticas y alertas |
| 📈 **Rendimiento** | Monitoreo de promedios, materias aprobadas y en riesgo |
| 🤝 **Voluntariado** | Registro de horas, actividades y estado de cumplimiento |
| 📊 **Reportes** | Generación de PDF profesional y exportación de datos |
| ⚙️ **Configuración** | Parámetros del sistema y constantes editables |

---

## 🛠 Tecnologías

- **Python 3.12+**
- **CustomTkinter** — Interfaz de escritorio moderna
- **Pandas + NumPy** — Manipulación de datos
- **OpenPyXL** — Lectura/escritura del archivo Excel
- **Matplotlib** — Gráficos embebidos en la aplicación
- **ReportLab** — Generación de reportes PDF
- **Pillow** — Soporte para imágenes de estudiantes
- **ttkbootstrap** — Estilos adicionales para la UI

---

## 🚀 Instalación y ejecución

### 1. Abrir el proyecto

```powershell
cd c:\Users\danie\OneDrive\Desktop\sistema_seguimiento_becas
```

### 2. Crear entorno virtual (recomendado)

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 4. Ejecutar la aplicación

```powershell
python main.py
```

> Al iniciar por primera vez, el sistema verifica el archivo `data/becados.xlsx`. Si está vacío o no existe, genera automáticamente datos de prueba para 100 estudiantes.

---

## 📁 Estructura del proyecto

```
├── main.py
├── config.py
├── requirements.txt
├── README.md
├── assets/
├── data/
│   ├── carreras_universidades.py
│   ├── generar_datos.py
│   ├── plantillas/
│   ├── backups/
│   └── becados.xlsx
├── exports/
├── images/
├── reports/
├── services/
│   ├── excel_manager.py
│   ├── estudiantes.py
│   ├── asistencia.py
│   ├── seguimiento.py
│   ├── voluntariado.py
│   ├── rendimiento.py
│   ├── indicadores.py
│   └── reportes.py
├── ui/
│   ├── app.py
│   ├── menu.py
│   ├── dashboard.py
│   ├── estudiantes.py
│   ├── seguimiento.py
│   ├── asistencia.py
│   ├── rendimiento.py
│   ├── voluntariado.py
│   ├── perfil.py
│   ├── reportes_view.py
│   ├── config_view.py
│   └── components/
│       └── cards.py
└── utils/
    └── logger.py
```

---

## 📊 Algoritmo de riesgo

El sistema calcula un índice de riesgo compuesto a partir de cuatro componentes:

| Dimensión | Peso | Qué mide |
|-----------|------|----------|
| Asistencia | 40% | Porcentaje de días asistidos |
| Promedio académico | 30% | Nota promedio sobre 10 |
| Voluntariado | 20% | Horas acumuladas frente a la meta |
| Seguimiento | 10% | Días desde el último contacto |

**Clasificación:**
- 🟢 **Bajo** — Índice ≤ 40%
- 🟡 **Medio** — Índice entre 40% y 70%
- 🔴 **Alto** — Índice > 70%

---

## 🗄 Estructura del Excel (`data/becados.xlsx`)

El archivo funciona como base de datos con las siguientes hojas:

1. **Estudiantes** — Datos personales y académicos
2. **Asistencias** — Registro diario de asistencia
3. **Voluntariado** — Actividades, horas y observaciones
4. **Seguimientos** — Historial de monitoreo y compromisos
5. **Rendimiento** — Promedios, materias aprobadas/reprobadas y riesgo
6. **Configuracion** — Parámetros de negocio y ajustes del sistema

---

## 📄 Reportes disponibles

- **Reporte individual**: PDF completo por estudiante
- **Reporte general**: Resumen global de todos los estudiantes
- **Reporte de riesgo**: Lista de estudiantes en riesgo medio o alto

---

## 🔒 Buenas prácticas implementadas

- Arquitectura en capas: UI ↔ Services ↔ Excel
- Código con **type hints** y separación de responsabilidades
- Logging de eventos y errores en `sistema_becas.log`
- Backups automáticos antes de escrituras en Excel
- Caché de lectura para mejorar rendimiento
- Operaciones de inicialización en hilo para no bloquear la UI
- Validaciones y manejo de errores para Excel en uso

---

## 📝 Notas adicionales

- `data/becados.xlsx` se crea y mantiene automáticamente.
- Los reportes PDF se generan en `reports/`.
- Las exportaciones se guardan en `exports/`.
- El archivo de configuración global es `config.py`.
- El generador de prueba se encuentra en `data/generar_datos.py`.
