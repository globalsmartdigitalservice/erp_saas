from django.conf import settings
from django.db import models

from core.tenancy import ModeloTenant


class SesionAcceso(ModeloTenant):


    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
    )

    resultado = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.RESULTADO_ACCESO",
    )


    ip = models.GenericIPAddressField(null=True, blank=True)

    
    dispositivo = models.ForeignKey(
        "seguridad.Dispositivo",
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
    )

    user_agent = models.CharField(max_length=400, blank=True)

    inicio = models.DateTimeField(auto_now_add=True)

    
    fin = models.DateTimeField(null=True, blank=True)


    refresh_jti = models.CharField(max_length=32, blank=True, db_index=True)

    estado = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.ESTADO_REGISTRO — soft delete, nunca se borra.",
    )

    class Meta:
        db_table = "segu_sesion_acceso"
        verbose_name = "Acceso"
        verbose_name_plural = "Accesos"
        ordering = ["-inicio"]
        indexes = [
            
            models.Index(
                fields=["usuario", "fin"], name="sesion_usuario_abierta_idx"
            ),
        ]

    @property
    def esta_abierta(self) -> bool:
        return self.fin is None

    def __str__(self):
        estado = "abierta" if self.esta_abierta else f"cerrada {self.fin}"
        return f"{self.usuario} {self.inicio:%Y-%m-%d %H:%M} ({estado})"
