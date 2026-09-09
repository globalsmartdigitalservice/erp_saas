from django.db import models

from ..managers import TraduccionManager


class Traduccion(models.Model):
    empresa = models.ForeignKey(
        "empresas.Empresa",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="+",
        help_text="Vacío = traducción de fábrica, igual para todas las empresas.",
    )


    entidad_tipo = models.CharField(max_length=100)

    entidad_id = models.IntegerField()

    campo = models.CharField(max_length=100)

    idioma = models.ForeignKey(
        "idiomas.Idioma",
        on_delete=models.CASCADE,
        related_name="traducciones",
    )

    texto = models.TextField()

    objects = TraduccionManager()

    class Meta:
        db_table = "idio_traduccion"
        verbose_name = "Traducción"
        verbose_name_plural = "Traducciones"
        ordering = ["entidad_tipo", "entidad_id", "campo"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "entidad_tipo", "entidad_id", "campo", "idioma"],
                name="traduccion_unica_por_empresa",
            ),
            models.UniqueConstraint(
                fields=["entidad_tipo", "entidad_id", "campo", "idioma"],
                condition=models.Q(empresa__isnull=True),
                name="traduccion_de_fabrica_unica",
            ),
        ]
        indexes = [
            models.Index(
                fields=["entidad_tipo", "campo", "idioma", "entidad_id"],
                name="traduccion_busqueda_por_lote",
            ),
        ]

    def __str__(self):
        return f"{self.entidad_tipo}.{self.campo}#{self.entidad_id} [{self.idioma_id}]"
