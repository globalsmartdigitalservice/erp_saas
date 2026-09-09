from django.db import models

from core.tenancy import ModeloTenant


class CategoriaEntidad(ModeloTenant):

    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, blank=True)

    descuento_categ_cliente = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    lista_precio_id = models.IntegerField(null=True, blank=True)

    estado = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.ESTADO_REGISTRO — soft delete, nunca se borra.",
    )

    class Meta:
        db_table = "ent_categoria_entidad"
        verbose_name = "Categoría de entidad"
        verbose_name_plural = "Categorías de entidad"
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "nombre"],
                name="categoria_entidad_nombre_unico_por_empresa",
            ),
        ]

    def __str__(self):
        return self.nombre
