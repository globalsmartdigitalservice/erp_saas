from django.db import models

from core.tenancy import ModeloTenant


class EmpresaMoneda(ModeloTenant):

    moneda = models.ForeignKey(
        "monedas.Moneda",
        on_delete=models.PROTECT,
        related_name="+",
    )

    es_moneda_oficial = models.BooleanField(default=False)

    estado = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
    )

    class Meta:
        db_table = "core_empresa_moneda"
        verbose_name = "Moneda de la empresa"
        verbose_name_plural = "Monedas de la empresa"
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "moneda"],
                name="empresa_moneda_unica",
            ),
        ]

    def __str__(self):
        marca = " (oficial)" if self.es_moneda_oficial else ""
        return f"empresa {self.empresa_id} opera con {self.moneda_id}{marca}"
