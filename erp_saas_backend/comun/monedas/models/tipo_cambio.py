from django.db import models

from core.tenancy import ModeloTenant


class TipoCambio(ModeloTenant):
    moneda_origen = models.ForeignKey(
        "monedas.Moneda",
        on_delete=models.PROTECT,
        related_name="+",
    )

    moneda_destino = models.ForeignKey(
        "monedas.Moneda",
        on_delete=models.PROTECT,
        related_name="+",
    )

    fecha = models.DateField()

    valor = models.DecimalField(max_digits=18, decimal_places=6)

    estado = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
    )

    class Meta:
        db_table = "core_tipo_cambio"
        verbose_name = "Tipo de cambio"
        verbose_name_plural = "Tipos de cambio"
        ordering = ["-fecha", "moneda_origen"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "moneda_origen", "moneda_destino", "fecha"],
                name="tipo_cambio_unico_por_empresa_par_fecha",
            ),
            models.CheckConstraint(
                condition=~models.Q(moneda_origen=models.F("moneda_destino")),
                name="tipo_cambio_origen_distinto_de_destino",
            ),
        ]
        indexes = [
            models.Index(
                fields=["empresa", "moneda_origen", "moneda_destino", "-fecha"],
                name="tipo_cambio_par_fecha_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.moneda_origen_id}→{self.moneda_destino_id} "
            f"{self.fecha}: {self.valor}"
        )
