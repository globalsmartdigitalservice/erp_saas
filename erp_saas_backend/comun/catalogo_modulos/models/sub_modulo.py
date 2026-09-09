from django.db import models


class SubModulo(models.Model):

    codigo = models.CharField(max_length=60, unique=True)

    modulo_sistema = models.ForeignKey(
        "catalogo_modulos.ModuloSistema",
        on_delete=models.PROTECT,
        related_name="sub_modulos",
    )

    nombre = models.CharField(max_length=100)


    ruta = models.CharField(max_length=200, unique=True)

    estado = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.ESTADO_REGISTRO — soft delete, nunca se borra.",
    )

    class Meta:
        db_table = "prov_sub_modulo"
        verbose_name = "Submódulo"
        verbose_name_plural = "Submódulos"
        ordering = ["modulo_sistema__codigo", "nombre"]
        constraints = [

            models.UniqueConstraint(
                fields=["modulo_sistema", "nombre"],
                name="sub_modulo_nombre_unico_por_modulo",
            ),
        ]

    def __str__(self):
        return f"{self.codigo} ({self.ruta})"
