"""
Sistema Inteligente de Seguimiento para Estudiantes Becados
Punto de entrada principal.
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path

# Ajuste de path para que todas las importaciones funcionen
sys.path.insert(0, str(Path(__file__).parent))

import customtkinter as ctk
from config import COLORS, FONTS, EXCEL_FILE
from utils.logger import logger


class SplashScreen(ctk.CTkToplevel):
    """Pantalla de carga inicial."""

    def __init__(self, master) -> None:
        super().__init__(master)
        self.overrideredirect(True)
        self.configure(fg_color=COLORS["bg_sidebar"])

        w, h = 480, 280
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

        ctk.CTkLabel(self, text="🎓", font=("Segoe UI Emoji", 56),
                     text_color=COLORS["primary"]).pack(pady=(40, 8))
        ctk.CTkLabel(self, text="Sistema Inteligente de Becados",
                     font=FONTS["heading_md"], text_color="white").pack()
        ctk.CTkLabel(self, text="Cargando datos y verificando archivo Excel...",
                     font=FONTS["body_sm"],
                     text_color=COLORS["text_light"]).pack(pady=(8, 20))

        self._bar = ctk.CTkProgressBar(self, width=360, mode="indeterminate")
        self._bar.pack()
        self._bar.start()

        self._status = ctk.CTkLabel(self, text="Inicializando...",
                                     font=FONTS["caption"],
                                     text_color=COLORS["text_light"])
        self._status.pack(pady=10)

    def set_status(self, msg: str) -> None:
        self._status.configure(text=msg)

    def close(self) -> None:
        self._bar.stop()
        self.destroy()


def _verificar_datos(splash: SplashScreen) -> None:
    """Verifica y genera datos de prueba si el Excel está vacío."""
    from services.excel_manager import ExcelManager
    from config import SHEET_ESTUDIANTES

    splash.after(0, lambda: splash.set_status("Verificando archivo Excel..."))
    excel = ExcelManager()

    df = excel.read_sheet(SHEET_ESTUDIANTES)
    if df.empty:
        splash.after(0, lambda: splash.set_status("Generando datos de prueba (100 estudiantes)..."))
        logger.info("Excel vacío, generando datos de prueba...")
        try:
            import importlib.util, os
            gen_path = Path(__file__).parent / "data" / "generar_datos.py"
            spec = importlib.util.spec_from_file_location("generar_datos", gen_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.main()
            logger.info("Datos de prueba generados.")
        except Exception as exc:
            logger.error("Error generando datos de prueba: %s", exc)
    else:
        splash.after(0, lambda: splash.set_status(
            f"✅ {len(df)} estudiantes encontrados en Excel."))


def main() -> None:
    logger.info("=== Iniciando Sistema Inteligente de Becados ===")

    # Root oculta mientras carga
    root = ctk.CTk()
    root.withdraw()
    root.update()

    splash = SplashScreen(root)
    splash.update()

    # Verificar/generar datos en hilo separado
    done = threading.Event()

    def _worker():
        _verificar_datos(splash)
        done.set()

    t = threading.Thread(target=_worker, daemon=True)
    t.start()

    # Esperar hasta que termine la inicialización
    def _wait_and_launch():
        if not done.is_set():
            root.after(100, _wait_and_launch)
            return
        splash.after(400, lambda: _launch(root, splash))

    root.after(100, _wait_and_launch)
    root.mainloop()


def _launch(root, splash: SplashScreen) -> None:
    """Lanza la aplicación principal."""
    splash.set_status("¡Listo! Abriendo la aplicación...")
    splash.after(500, lambda: _open_app(root, splash))


def _open_app(root, splash: SplashScreen) -> None:
    splash.close()
    root.destroy()

    from ui.app import App
    app = App()
    logger.info("Aplicación iniciada correctamente.")
    app.mainloop()
    logger.info("Aplicación cerrada.")


if __name__ == "__main__":
    main()
