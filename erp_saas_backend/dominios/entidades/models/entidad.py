from django.db import models

from core.tenancy import ModeloTenant


class Entidad(ModeloTenant):

    tipo_entidad = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.TIPO_ENTIDAD",
    )

    nombre = models.CharField(max_length=200)

    pri_apellido = models.CharField(max_length=100, blank=True)
    seg_apellido = models.CharField(max_length=100, blank=True)

    tipo_documento = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.TIPO_DOCUMENTO",
    )

    documento = models.CharField(max_length=50, blank=True)

    regimen_tributario = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
        help_text="AGRUPADOR.REGIMEN_TRIBUTARIO",
    )

    estado = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.ESTADO_REGISTRO — soft delete, nunca se borra.",
    )

    class Meta:
        db_table = "ent_entidad"
        verbose_name = "Entidad"
        verbose_name_plural = "Entidades"
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "documento"],
                condition=~models.Q(documento=""),
                name="entidad_documento_unico_por_empresa",
            ),
        ]

    def __str__(self):
        partes = [self.nombre, self.pri_apellido, self.seg_apellido]
        return " ".join(p for p in partes if p)
