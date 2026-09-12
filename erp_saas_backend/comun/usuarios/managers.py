from django.contrib.auth.models import UserManager
from django.core.exceptions import ValidationError


class UsuarioManager(UserManager):
    """Una cuenta sin cliente es del proveedor; las demás dicen de quién son."""

    def create_user(self, username, email=None, password=None, **extra_fields):
        if not (extra_fields.get("matriz") or extra_fields.get("matriz_id")):
            raise ValidationError("Falta indicar de qué cliente es esta cuenta.")
        return super().create_user(username, email, password, **extra_fields)


__all__ = ["UsuarioManager"]
