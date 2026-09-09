from django.db import models


class Pais(models.Model):
    cod_pais = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=100)
    codigo_iso = models.CharField(max_length=3, unique=True)

    estado = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
    )

    class Meta:
        db_table = "core_pais"
        verbose_name = "País"
        verbose_name_plural = "Países"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
