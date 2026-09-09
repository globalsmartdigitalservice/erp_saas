from django.db import models

from core.tenancy import ModeloTenant


class ReferenciaCruzada(ModeloTenant):

    modulo_origen = models.CharField(max_length=30)
    tabla_origen = models.CharField(max_length=63)
    registro_origen_id = models.IntegerField()

    modulo_destino = models.CharField(max_length=30)
    tabla_destino = models.CharField(max_length=63)
    registro_destino_id = models.IntegerField()

    tipo_vinculo = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.TIPO_VINCULO — genera, respalda, deriva de…",
    )

    estado = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.ESTADO_REGISTRO — soft delete, nunca se borra.",
    )

    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "serv_referencia_cruzada"
        verbose_name = "Referencia cruzada"
        verbose_name_plural = "Referencias cruzadas"
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "empresa",
                    "tabla_origen",
                    "registro_origen_id",
                    "tabla_destino",
                    "registro_destino_id",
                    "tipo_vinculo",
                ],
                name="referencia_cruzada_sin_repetir",
            ),
        ]
        indexes = [
            models.Index(
                fields=["empresa", "tabla_origen", "registro_origen_id"],
                name="ref_cruzada_por_origen",
            ),
            models.Index(
                fields=["empresa", "tabla_destino", "registro_destino_id"],
                name="ref_cruzada_por_destino",
            ),
        ]

    def __str__(self):
        return (
            f"{self.tabla_origen}#{self.registro_origen_id} → "
            f"{self.tabla_destino}#{self.registro_destino_id}"
        )
