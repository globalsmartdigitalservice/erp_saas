"""Afiliar desde un test, donde no hay sesión.

`membresias.afiliar()` toma la empresa de donde está parado quien llama, así
que hay que decirlo explícito.
"""

from comun.membresias import api as membresias
from core.tenancy import empresa


def afiliar_en(empresa_id: int, **campos):
    with empresa(empresa_id):
        return membresias.afiliar(**campos)


def afiliar_al_grupo_desde(empresa_id: int, **campos):
    with empresa(empresa_id):
        return membresias.afiliar_al_grupo(**campos)


__all__ = ["afiliar_en", "afiliar_al_grupo_desde"]
