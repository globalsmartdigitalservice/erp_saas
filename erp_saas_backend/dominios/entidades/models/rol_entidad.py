from django.db import models

from core.tenancy import ModeloTenantDerivado


class RolEntidad(ModeloTenantDerivado):
    RUTA_A_EMPRESA = "entidad"

    entidad = models.ForeignKey(
        "entidades.Entidad",
        on_delete=models.PROTECT,
        related_name="+",
    )

    tipo_rol = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.TIPO_ROL",
    )

    categoria_entidad = models.ForeignKey(
        "entidades.CategoriaEntidad",
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
    )


    limite_credito = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
    )

    datos_rol = models.JSONField(default=dict, blank=True)

    estado = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.ESTADO_REGISTRO — soft delete, nunca se borra.",
    )

    class Meta:
        db_table = "ent_rol_entidad"
        verbose_name = "Rol de la entidad"
        verbose_name_plural = "Roles de la entidad"
        constraints = [
            models.UniqueConstraint(
                fields=["entidad", "tipo_rol"],
                name="rol_entidad_sin_repetir_el_rol",
            ),
        ]

    def __str__(self):
        return f"entidad {self.entidad_id} como {self.tipo_rol_id}"
