from django.db import models


class ModuloSistema(models.Model):

    codigo = models.CharField(max_length=30, unique=True)

    nombre = models.CharField(max_length=100)

    version = models.CharField(max_length=20, blank=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    es_vendible = models.BooleanField(default=False)

    estado = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.ESTADO_REGISTRO — soft delete, nunca se borra.",
    )

    class Meta:
        db_table = "prov_modulo_sistema"
        verbose_name = "Módulo del sistema"
        verbose_name_plural = "Módulos del sistema"
        ordering = ["codigo"]

    def __str__(self):
        marca = " (vendible)" if self.es_vendible else ""
        return f"{self.codigo}{marca}"
