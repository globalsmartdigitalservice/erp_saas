"""
Entorno de test.

Hereda de `local` y solo cambia lo que en los tests tiene que
comportarse distinto. Es lo que `pytest.ini` apunta con `--ds`.
"""

from .local import *  # noqa: F401,F403


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Los tests corren con la puerta CERRADA, como producción. Con la de
# desarrollo, un guard que aceptara la cookie de Django pasaría los tests y
# fallaría donde importa.
TRUST_DJANGO_SESSION = False
