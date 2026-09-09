from django.conf import settings
from django.db import models

from core.tenancy import ModeloTenantDerivado


class DispositivoUsuario(ModeloTenantDerivado):
    RUTA_A_EMPRESA = "usuario_empresa"

    usuario_empresa = models.ForeignKey(
        "membresias.UsuarioEmpresa",
        on_delete=models.CASCADE,
        related_name="dispositivos",
    )

    dispositivo = models.ForeignKey(
        "seguridad.Dispositivo",
        on_delete=models.PROTECT,
        related_name="autorizaciones",
    )


    autorizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
    )

    fecha_autorizacion = models.DateTimeField(auto_now_add=True)

    ultimo_acceso = models.DateTimeField(null=True, blank=True)


    ultima_ip = models.GenericIPAddressField(null=True, blank=True)

    fecha_inicio = models.DateField("desde")

    fecha_fin = models.DateField("hasta", null=True, blank=True)

    estado = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.ESTADO_REGISTRO — soft delete, nunca se borra.",
    )

    class Meta:
        db_table = "segu_dispositivo_usuario"
        verbose_name = "Dispositivo autorizado"
        verbose_name_plural = "Dispositivos autorizados"
        ordering = ["-fecha_inicio"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(fecha_fin__isnull=True)
                | models.Q(fecha_fin__gte=models.F("fecha_inicio")),
                name="dispositivo_usuario_fechas_coherentes",
            ),
        ]

    def __str__(self):
        return f"{self.usuario_empresa} ← {self.dispositivo}"
