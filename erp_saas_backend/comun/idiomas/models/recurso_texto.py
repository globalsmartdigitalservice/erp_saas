from django.db import models


class RecursoTexto(models.Model):
    clave = models.CharField(max_length=200)
    idioma = models.ForeignKey(
        "idiomas.Idioma",
        on_delete=models.CASCADE,
        related_name="textos",
    )
    texto = models.TextField()
    modulo = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "idio_recurso_texto"
        verbose_name = "Recurso de texto"
        verbose_name_plural = "Recursos de texto"
        ordering = ["modulo", "clave"]
        constraints = [
            models.UniqueConstraint(
                fields=["clave", "idioma"],
                name="recurso_texto_unico_por_clave_idioma",
            ),
        ]

    def __str__(self):
        return f"{self.clave} [{self.idioma.codigo}]"
