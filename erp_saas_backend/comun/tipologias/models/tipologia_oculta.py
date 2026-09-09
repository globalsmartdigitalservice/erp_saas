from django.db import models


class TipologiaOculta(models.Model):
    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.CASCADE,
        related_name="+",
    )
    tipologia = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.CASCADE,
        related_name="+",
    )

    class Meta:
        db_table = "conf_tipologia_oculta"
        verbose_name = "Tipología oculta para la empresa"
        verbose_name_plural = "Tipologías ocultas para la empresa"
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "tipologia"],
                name="tipologia_oculta_unica",
            ),
        ]
        indexes = [
            models.Index(fields=["empresa", "tipologia"]),
        ]

    def __str__(self):
        return f"empresa {self.empresa_id} oculta la tipología {self.tipologia_id}"
