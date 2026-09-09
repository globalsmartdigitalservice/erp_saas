from django.db import models

from ..managers import TipologiaManager


class Tipologia(models.Model):
    class Estado(models.IntegerChoices):
        INACTIVO = 0, "Inactivo"
        ACTIVO = 1, "Activo"

    empresa = models.ForeignKey(
        "empresas.Empresa",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="+",
        help_text="Vacío = catálogo del sistema, igual para todas las empresas.",
    )

    agrupador = models.IntegerField(db_index=True)

    indice = models.IntegerField(default=0)

    nombre = models.CharField(max_length=100)
    abreviatura = models.CharField(max_length=20, blank=True)

    estado = models.IntegerField(choices=Estado, default=Estado.ACTIVO)

    objects = TipologiaManager()

    class Meta:
        db_table = "conf_tipologia"
        verbose_name = "Tipología"
        verbose_name_plural = "Tipologías"
        ordering = ["agrupador", "indice", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "agrupador", "nombre"],
                name="tipologia_unica_por_empresa_agrupador",
            ),
        ]
        indexes = [
            models.Index(fields=["empresa", "agrupador"]),
        ]

    def __str__(self):
        return self.nombre
