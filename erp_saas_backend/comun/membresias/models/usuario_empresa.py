from django.conf import settings
from django.db import models

from core.tenancy import ModeloTenant


class UsuarioEmpresa(ModeloTenant):

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="membresias",
    )

    fecha_asignacion = models.DateField("fecha de asignación")

    fecha_finalizacion = models.DateField(
        "fecha de finalización", null=True, blank=True
    )

    estado = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.ESTADO_REGISTRO — soft delete, nunca se borra.",
    )

    class Meta:
        db_table = "segu_usuario_empresa"
        verbose_name = "Membresía"
        verbose_name_plural = "Membresías"
        ordering = ["-fecha_asignacion"]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "empresa"],
                name="usuario_empresa_unica",
            ),
        ]

    def __str__(self):
        return f"{self.usuario.username} en {self.empresa}"
