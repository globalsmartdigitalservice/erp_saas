from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.tenancy import ModeloTenantDerivado


class HorarioAcceso(ModeloTenantDerivado):
    RUTA_A_EMPRESA = "usuario_empresa"

    usuario_empresa = models.ForeignKey(
        "membresias.UsuarioEmpresa",
        on_delete=models.CASCADE,
        related_name="horarios",
    )


    dia_semana = models.PositiveSmallIntegerField(
        "día de la semana",
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        help_text="0 = lunes … 6 = domingo (convención de date.weekday()).",
    )

    hora_inicio = models.TimeField("desde")

  
    hora_fin = models.TimeField("hasta")

    vigencia_desde = models.DateField()

    vigencia_hasta = models.DateField(null=True, blank=True)

    estado = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.ESTADO_REGISTRO — soft delete, nunca se borra.",
    )

    class Meta:
        db_table = "segu_horario_acceso"
        verbose_name = "Horario de acceso"
        verbose_name_plural = "Horarios de acceso"
        ordering = ["dia_semana", "hora_inicio"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(vigencia_hasta__isnull=True)
                | models.Q(vigencia_hasta__gte=models.F("vigencia_desde")),
                name="horario_acceso_vigencia_coherente",
            ),
        ]

    @property
    def cruza_medianoche(self) -> bool:
        return self.hora_fin < self.hora_inicio

    def __str__(self):
        dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        return f"{dias[self.dia_semana]} {self.hora_inicio}–{self.hora_fin}"
