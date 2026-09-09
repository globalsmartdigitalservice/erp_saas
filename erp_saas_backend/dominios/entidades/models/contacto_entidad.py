from django.db import models

from core.tenancy import ModeloTenantDerivado


class ContactoEntidad(ModeloTenantDerivado):
    RUTA_A_EMPRESA = "entidad"

    entidad = models.ForeignKey(
        "entidades.Entidad",
        on_delete=models.CASCADE,
        related_name="+",
    )

    nombre = models.CharField(max_length=200)
    cargo = models.CharField(max_length=100, blank=True)
    email = models.EmailField(max_length=254, blank=True)
    telefono = models.CharField(max_length=50, blank=True)

    estado = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.ESTADO_REGISTRO — soft delete, nunca se borra.",
    )

    class Meta:
        db_table = "ent_contacto_entidad"
        verbose_name = "Contacto de la entidad"
        verbose_name_plural = "Contactos de la entidad"

    def __str__(self):
        return f"{self.nombre} ({self.cargo})" if self.cargo else self.nombre
