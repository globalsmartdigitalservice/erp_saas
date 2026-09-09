from django.db import models

from core.tenancy import ModeloTenantDerivado


class Correlativo(ModeloTenantDerivado):
    RUTA_A_EMPRESA = "serie_documental"

    serie_documental = models.ForeignKey(
        "numeracion.SerieDocumental",
        on_delete=models.PROTECT,
        related_name="+",
    )

    gestion = models.IntegerField()

    ultimo_numero = models.IntegerField(default=0)

    class Meta:
        db_table = "serv_correlativo"
        verbose_name = "Correlativo"
        verbose_name_plural = "Correlativos"
        constraints = [
            models.UniqueConstraint(
                fields=["serie_documental", "gestion"],
                name="correlativo_unico_por_serie_y_gestion",
            ),
        ]

    def __str__(self):
        return f"serie {self.serie_documental_id} · {self.gestion}: {self.ultimo_numero}"
