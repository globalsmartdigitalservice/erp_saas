from django.db import models

from core.tenancy import ModeloTenantDerivado


class HorarioExcepcion(ModeloTenantDerivado):
    RUTA_A_EMPRESA = "usuario_empresa"

    usuario_empresa = models.ForeignKey(
        "membresias.UsuarioEmpresa",
        on_delete=models.CASCADE,
        related_name="excepciones",
    )

    fecha = models.DateField()


    hora_inicio = models.TimeField("desde", null=True, blank=True)
    hora_fin = models.TimeField("hasta", null=True, blank=True)

    tipo = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.TIPO_EXCEPCION_HORARIO — PERMISO o BLOQUEO.",
    )

    motivo = models.CharField(max_length=200, blank=True)

    creado_por = models.ForeignKey(
        "membresias.UsuarioEmpresa",
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
    )

    estado = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.ESTADO_REGISTRO — soft delete, nunca se borra.",
    )

    class Meta:
        db_table = "segu_horario_excepcion"
        verbose_name = "Excepción de horario"
        verbose_name_plural = "Excepciones de horario"
        ordering = ["-fecha"]
        constraints = [
           
            models.CheckConstraint(
                condition=(
                    models.Q(hora_inicio__isnull=True, hora_fin__isnull=True)
                    | models.Q(hora_inicio__isnull=False, hora_fin__isnull=False)
                ),
                name="horario_excepcion_horas_completas",
            ),
        ]

    @property
    def es_dia_completo(self) -> bool:
        return self.hora_inicio is None

    def __str__(self):
        cuando = "todo el día" if self.es_dia_completo else (
            f"{self.hora_inicio}–{self.hora_fin}"
        )
        return f"{self.fecha} {cuando} ({self.motivo or 'sin motivo'})"
