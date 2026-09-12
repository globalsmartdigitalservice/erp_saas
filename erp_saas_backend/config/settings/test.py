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
