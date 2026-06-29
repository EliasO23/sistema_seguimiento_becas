"""Configuración centralizada de logging."""

import logging
import sys
from pathlib import Path
from config import LOG_FILE, LOG_LEVEL


def setup_logger(name: str = "SistemaBecas") -> logging.Logger:
    """Crea y configura un logger reutilizable."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # ya configurado

    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler para archivo
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # Handler para consola
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return logger


logger = setup_logger()
