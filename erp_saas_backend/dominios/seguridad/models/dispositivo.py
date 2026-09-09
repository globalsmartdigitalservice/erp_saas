from django.db import models

from core.tenancy import ModeloTenant


class Dispositivo(ModeloTenant):


    tipo = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.TIPO_DISPOSITIVO",
    )

    nombre = models.CharField(max_length=100)

 
    identificador = models.CharField(max_length=100, blank=True)

  
    ip = models.GenericIPAddressField(null=True, blank=True)

    mac = models.CharField(max_length=17, blank=True)

    estado = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.ESTADO_REGISTRO — soft delete, nunca se borra.",
    )

    class Meta:
        db_table = "segu_dispositivo"
        verbose_name = "Dispositivo"
        verbose_name_plural = "Dispositivos"
        ordering = ["nombre"]
        constraints = [
 
            models.UniqueConstraint(
                fields=["empresa", "mac"],
                condition=~models.Q(mac=""),
                name="dispositivo_mac_unica_por_empresa",
            ),
   
            models.UniqueConstraint(
                fields=["empresa", "identificador"],
                condition=~models.Q(identificador=""),
                name="dispositivo_identificador_unico_por_empresa",
            ),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.mac or 'sin MAC'})"
