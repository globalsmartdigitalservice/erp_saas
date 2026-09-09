from django.db import models


class ModuloDependencia(models.Model):
    class Tipo(models.TextChoices):

        DURA = "DURA", "Dura — no funciona sin él"
        SUAVE = "SUAVE", "Suave — se integra si está"

    modulo = models.ForeignKey(
        "catalogo_modulos.ModuloSistema",
        on_delete=models.CASCADE,
        related_name="+",
        help_text="El módulo que declara la dependencia.",
    )

    depende_de = models.ForeignKey(
        "catalogo_modulos.ModuloSistema",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="El módulo requerido para que el primero funcione.",
    )
    tipo = models.CharField(max_length=10, choices=Tipo, default=Tipo.DURA)

    class Meta:
        db_table = "prov_modulo_dependencia"
        verbose_name = "Dependencia entre módulos"
        verbose_name_plural = "Dependencias entre módulos"
        constraints = [
            models.UniqueConstraint(
                fields=["modulo", "depende_de"],
                name="modulo_dependencia_sin_repetir",
            ),

            models.CheckConstraint(
                condition=~models.Q(modulo=models.F("depende_de")),
                name="modulo_dependencia_no_se_depende_de_si_mismo",
            ),
        ]

    def __str__(self):
        return f"{self.modulo_id} necesita {self.depende_de_id} ({self.tipo})"
