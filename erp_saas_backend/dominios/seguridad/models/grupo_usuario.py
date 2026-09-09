from django.conf import settings
from django.db import models

from core.tenancy import ModeloTenantDerivado


class GrupoUsuario(ModeloTenantDerivado):
    RUTA_A_EMPRESA = "usuario_empresa"

    usuario_empresa = models.ForeignKey(
        "membresias.UsuarioEmpresa",
        on_delete=models.CASCADE,
        related_name="roles",
    )

    grupo_empresa = models.ForeignKey(
        "seguridad.GrupoEmpresa",
        on_delete=models.PROTECT,
        related_name="asignaciones",
    )

 
    asignado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
    )

    fecha_inicio = models.DateField("desde")

    fecha_fin = models.DateField("hasta", null=True, blank=True)

    motivo = models.CharField(max_length=200, blank=True)

    estado = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.ESTADO_REGISTRO — soft delete, nunca se borra.",
    )

    class Meta:
        db_table = "segu_grupo_usuario"
        verbose_name = "Rol asignado"
        verbose_name_plural = "Roles asignados"
        ordering = ["-fecha_inicio"]
        constraints = [

            models.CheckConstraint(
                condition=models.Q(fecha_fin__isnull=True)
                | models.Q(fecha_fin__gte=models.F("fecha_inicio")),
                name="grupo_usuario_fechas_coherentes",
            ),
        ]

    def __str__(self):
        return f"{self.usuario_empresa} → {self.grupo_empresa.nombre}"
