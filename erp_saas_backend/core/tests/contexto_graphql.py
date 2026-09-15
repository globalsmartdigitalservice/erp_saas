"""El `context_value` de Strawberry, para tests.

Los guards leen `info.context.request.user`: sin esto, una mutation
protegida no se puede llamar desde un test.

Pone también `usuario_del_token`, la marca que deja el middleware del ERP,
porque esto simula una sesión del ERP y no la cookie del `/admin/`. Sin la
marca, con `TRUST_DJANGO_SESSION` apagado —que es como corren los tests— toda
mutation protegida respondería "Debe iniciar sesión"."""


class _Request:
    def __init__(self, usuario):
        self.user = usuario
        self.usuario_del_token = usuario
        self.META = {}
        self.COOKIES = {}


class Contexto:
    def __init__(self, usuario):
        self.request = _Request(usuario)
        self.response = None


__all__ = ["Contexto"]
