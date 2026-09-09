from django.db import models

from dominios.seguridad.managers import GrupoEmpresaManager


class GrupoEmpresa(models.Model):
    
    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.PROTECT,
        related_name="+",
        db_index=True,
    )

    nombre = models.CharField(max_length=100)

    estado = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.ESTADO_REGISTRO — soft delete, nunca se borra.",
    )

    objects = GrupoEmpresaManager()

    class Meta:
        db_table = "segu_grupo_empresa"
        verbose_name = "Rol de empresa"
        verbose_name_plural = "Roles de empresa"
        ordering = ["nombre"]
        constraints = [

            models.UniqueConstraint(
                fields=["empresa", "nombre"],
                name="grupo_empresa_nombre_unico",
            ),
        ]

    def __str__(self):
        return self.nombre
