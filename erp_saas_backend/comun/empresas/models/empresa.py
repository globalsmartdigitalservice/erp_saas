from django.db import models


class Empresa(models.Model):
    empresa_padre = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="sucursales",
    )

    ident_tributaria = models.CharField(max_length=30, db_index=True)
    razon_social = models.CharField(max_length=200)
    nombre_comercial = models.CharField(max_length=200, blank=True)

    tipo_empresa = models.ForeignKey(
        "tipologias.Tipologia", on_delete=models.PROTECT, related_name="+"
    )
    rubro = models.ForeignKey(
        "tipologias.Tipologia", on_delete=models.PROTECT, related_name="+"
    )
    estado = models.ForeignKey(
        "tipologias.Tipologia", on_delete=models.PROTECT, related_name="+"
    )

    ubicacion_geografica = models.ForeignKey(
        "geografia.UbicacionGeografica",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="+",
    )
    idioma_default = models.ForeignKey(
        "idiomas.Idioma", on_delete=models.PROTECT, related_name="+"
    )


    class Meta:
        db_table = "core_empresa"
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ["razon_social"]

    def __str__(self):
        return self.nombre_comercial or self.razon_social

    @property
    def es_matriz(self) -> bool:
        return self.empresa_padre_id is None
