from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower

from comun.usuarios.managers import UsuarioManager


class Usuario(AbstractUser):

    matriz = models.ForeignKey(
        "empresas.Empresa",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="+",
    )

    email = models.EmailField("correo")

    first_name = models.CharField("nombres", max_length=150, blank=True)
    last_name = models.CharField("apellido paterno", max_length=150, blank=True)

    seg_apellido = models.CharField("apellido materno", max_length=150, blank=True)

    debe_cambiar_password = models.BooleanField(
        "debe cambiar la contraseña", default=False
    )

    idioma = models.ForeignKey(
        "idiomas.Idioma",
        verbose_name="idioma preferido",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="+",
    )

    objects = UsuarioManager()

    class Meta:
        db_table = "segu_usuario"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["username"]
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                "matriz",
                name="usuario_correo_unico_por_cliente",
            ),
            models.UniqueConstraint(
                Lower("email"),
                condition=models.Q(matriz__isnull=True),
                name="usuario_correo_unico_sin_cliente",
            ),
            models.CheckConstraint(
                condition=models.Q(is_staff=False) | models.Q(matriz__isnull=True),
                name="solo_el_proveedor_entra_al_admin",
            ),
        ]

    def save(self, *args, **kwargs):
        # Se normaliza acá y no en el service: `createsuperuser`, las semillas
        # y el /admin/ no pasan por el service.
        self.email = (self.email or "").strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.email})"

    def get_full_name(self):
        partes = (self.first_name, self.last_name, self.seg_apellido)
        return " ".join(p for p in partes if p)
