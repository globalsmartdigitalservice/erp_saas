"""
Entorno de test.

Hoy es igual que `local` y no agrega nada. Se mantiene como archivo
propio porque es lo que `pytest.ini` apunta con `--ds`, y porque el día
que el test necesite algo distinto —un backend de mail falso, una caché
en memoria— va acá y no en `local`.
"""

from .local import *  # noqa: F401,F403
