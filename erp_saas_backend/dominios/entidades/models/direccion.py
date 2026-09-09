from django.db import models

from core.tenancy import ModeloTenantDerivado


class Direccion(ModeloTenantDerivado):
    RUTA_A_EMPRESA = "entidad"

    entidad = models.ForeignKey(
        "entidades.Entidad",
        on_delete=models.CASCADE,
        related_name="+",
    )

    tipo = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.TIPO_DIRECCION",
    )

    calle = models.CharField(max_length=200, blank=True)
    numero = models.CharField(max_length=20, blank=True)
    descripcion = models.CharField(max_length=255, blank=True)

    ubicacion_geografica = models.ForeignKey(
        "geografia.UbicacionGeografica",
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
    )

    direccion_texto = models.CharField(max_length=255, blank=True)

    latitud = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitud = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

    estado = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.ESTADO_REGISTRO — soft delete, nunca se borra.",
    )

    class Meta:
        db_table = "ent_direccion"
        verbose_name = "Dirección"
        verbose_name_plural = "Direcciones"

    def __str__(self):
        escrita = self.direccion_texto or f"{self.calle} {self.numero}".strip()
        return escrita or f"dirección {self.pk}"
