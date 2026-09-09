from django.db import models

from core.tenancy import ModeloTenant


class TipoDocumentoComercial(ModeloTenant):

    codigo = models.CharField(max_length=20)

    nombre = models.CharField(max_length=100)

    afecta_stock = models.BooleanField(default=False)
    genera_ingreso = models.BooleanField(default=False)
    es_venta = models.BooleanField(default=False)

    estado = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.ESTADO_REGISTRO — soft delete, nunca se borra.",
    )

    class Meta:
        db_table = "vent_tipo_documento_comercial"
        verbose_name = "Tipo de documento comercial"
        verbose_name_plural = "Tipos de documento comercial"
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "codigo"],
                name="tipo_documento_codigo_unico_por_empresa",
            ),
        ]

    def __str__(self):
        return f"{self.codigo} — {self.nombre}"
