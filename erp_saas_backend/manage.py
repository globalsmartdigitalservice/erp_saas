#!/usr/bin/env python
"""Utilidad de línea de comandos de Django."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Se carga el .env ANTES de elegir el settings, para que
# DJANGO_SETTINGS_MODULE definido ahí tenga prioridad.
load_dotenv(Path(__file__).resolve().parent / ".env")


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. ¿Está instalado y el entorno "
            "virtual activado?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
