from django.db import models


class Funcionalidad(models.Model):
    sub_modulo = models.ForeignKey(
        "catalogo_modulos.SubModulo",
        on_delete=models.PROTECT,
        related_name="funcionalidades",
    )

    auth_permission = models.OneToOneField(
        "auth.Permission",
        on_delete=models.PROTECT,
        related_name="funcionalidad",
    )

    nombre = models.CharField(max_length=100)


    descripcion = models.CharField(max_length=300, blank=True)

    estado = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.ESTADO_REGISTRO — soft delete, nunca se borra.",
    )

    class Meta:
        db_table = "prov_funcionalidad"
        verbose_name = "Funcionalidad"
        verbose_name_plural = "Funcionalidades"
        ordering = ["sub_modulo__codigo", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["sub_modulo", "nombre"],
                name="funcionalidad_nombre_unico_por_pantalla",
            ),
        ]

    def __str__(self):
        return f"{self.sub_modulo.codigo}: {self.nombre}"
