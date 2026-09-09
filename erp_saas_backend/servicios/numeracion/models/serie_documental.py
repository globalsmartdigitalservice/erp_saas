from django.db import models

from core.tenancy import ModeloTenant


class SerieDocumental(ModeloTenant):

    tipo_documento = models.ForeignKey(
        "tipos_documento.TipoDocumentoComercial",
        on_delete=models.PROTECT,
        related_name="+",
    )

    prefijo = models.CharField(max_length=20, blank=True)

    estado = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.ESTADO_REGISTRO — soft delete, nunca se borra.",
    )

    class Meta:
        db_table = "serv_serie_documental"
        verbose_name = "Serie documental"
        verbose_name_plural = "Series documentales"
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "tipo_documento", "prefijo"],
                name="serie_documental_unica_por_tipo_y_prefijo",
            ),
        ]

    def __str__(self):
        return f"{self.prefijo or '(sin prefijo)'} · tipo {self.tipo_documento_id}"
