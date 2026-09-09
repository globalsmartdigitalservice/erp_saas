from django.db import models


class UbicacionGeografica(models.Model):
    pais = models.ForeignKey(
        "geografia.Pais",
        on_delete=models.PROTECT,
        related_name="ubicaciones",
    )
    division_superior = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="divisiones",
    )

    codigo = models.CharField(max_length=20, blank=True)
    nombre = models.CharField(max_length=150)
    tipo = models.CharField(max_length=50)
    nivel = models.IntegerField(default=1)

    estado = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
    )

    class Meta:
        db_table = "core_ubicacion_geografica"
        verbose_name = "Ubicación geográfica"
        verbose_name_plural = "Ubicaciones geográficas"
        ordering = ["pais", "nivel", "nombre"]
        indexes = [
            models.Index(fields=["pais", "nivel"]),
            models.Index(fields=["division_superior"]),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.tipo})"
