from django.db import models


class Moneda(models.Model):
    descripcion = models.CharField(max_length=100)
    codigo = models.CharField(max_length=3, unique=True)
    simbolo = models.CharField(max_length=5, blank=True)

    estado = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
    )

    class Meta:
        db_table = "core_moneda"
        verbose_name = "Moneda"
        verbose_name_plural = "Monedas"
        ordering = ["codigo"]

    def __str__(self):
        return f"{self.codigo} — {self.descripcion}"
