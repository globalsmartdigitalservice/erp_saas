"""El `context_value` de Strawberry, para tests.

Los guards leen `info.context.request.user`: sin esto, una mutation
protegida no se puede llamar desde un test."""


class _Peticion:
    def __init__(self, usuario):
        self.user = usuario
        self.META = {}
        self.COOKIES = {}


class Contexto:
    def __init__(self, usuario):
        self.request = _Peticion(usuario)
        self.response = None


__all__ = ["Contexto"]
