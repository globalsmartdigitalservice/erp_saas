from django.db import models

from core.tenancy import ModeloTenantDerivado


class EncuestaSatisfaccion(ModeloTenantDerivado):
    RUTA_A_EMPRESA = "entidad"

    entidad = models.ForeignKey(
        "entidades.Entidad",
        on_delete=models.PROTECT,
        related_name="+",
    )

    fecha = models.DateField()

    puntaje = models.IntegerField()

    comentario = models.TextField(blank=True)

    class Meta:
        db_table = "ent_encuesta_satisfaccion"
        verbose_name = "Encuesta de satisfacción"
        verbose_name_plural = "Encuestas de satisfacción"

    def __str__(self):
        return f"entidad {self.entidad_id}: {self.puntaje} ({self.fecha})"
