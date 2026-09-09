from django.db import models


class EmpresaAgrupador(models.Model):
    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.CASCADE,
        related_name="+",
    )

    agrupador = models.IntegerField()

    class Meta:
        db_table = "conf_empresa_agrupador"
        verbose_name = "Lista ampliable por la empresa"
        verbose_name_plural = "Listas ampliables por la empresa"
        ordering = ["empresa", "agrupador"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "agrupador"],
                name="empresa_agrupador_unico",
            ),
        ]

    def __str__(self):
        return f"empresa {self.empresa_id} puede ampliar la lista {self.agrupador}"
