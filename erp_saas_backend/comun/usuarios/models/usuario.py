from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):

    email = models.EmailField("correo", unique=True)

    first_name = models.CharField("nombres", max_length=150, blank=True)
    last_name = models.CharField("apellido paterno", max_length=150, blank=True)

    seg_apellido = models.CharField("apellido materno", max_length=150, blank=True)

    debe_cambiar_password = models.BooleanField(
        "debe cambiar la contraseña", default=False
    )

    class Meta:
        db_table = "segu_usuario"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["username"]

    def __str__(self):
        return f"{self.username} ({self.email})"

    def get_full_name(self):
        partes = (self.first_name, self.last_name, self.seg_apellido)
        return " ".join(p for p in partes if p)
