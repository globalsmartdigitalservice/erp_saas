from django.db import models

from core.tenancy import ModeloTenant


class EmpresaPais(ModeloTenant):

    pais = models.ForeignKey(
        "geografia.Pais",
        on_delete=models.PROTECT,
        related_name="+",
    )
    ubicacion_geografica = models.ForeignKey(
        "geografia.UbicacionGeografica",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="+",
    )

    direccion = models.CharField(max_length=255, blank=True)
    latitud = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitud = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    telefono = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    sitio_web = models.URLField(blank=True)
    logo = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "core_empresa_pais"
        verbose_name = "País de la empresa"
        verbose_name_plural = "Países de la empresa"
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "pais"],
                name="empresa_pais_unico",
            ),
        ]

    def __str__(self):
        return f"{self.empresa_id} en {self.pais}"
