from django.db import models


class Idioma(models.Model):
    codigo = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=50)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "idio_idioma"
        verbose_name = "Idioma"
        verbose_name_plural = "Idiomas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
