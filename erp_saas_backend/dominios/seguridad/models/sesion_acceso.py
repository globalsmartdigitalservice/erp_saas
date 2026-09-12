import datetime

from django.conf import settings
from django.db import models

from core.tenancy import ModeloTenantDerivado


class SesionAcceso(ModeloTenantDerivado):
    RUTA_A_EMPRESA = "usuario_empresa"

    #  Cuelga de la MEMBRESÍA y no de la cuenta: una sesión siempre es de
    # alguien trabajando en una empresa. Así, cuando lo dan de baja de esa
    # empresa, la sesión se puede dar cuenta.
    #
    # PROTECT y no CASCADE como sus hermanas: un rol asignado no significa
    # nada sin la membresía, pero esto es el registro histórico de quién
    # entró y cuándo.
    usuario_empresa = models.ForeignKey(
        "membresias.UsuarioEmpresa",
        on_delete=models.PROTECT,
        related_name="+",
    )

    resultado = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.RESULTADO_ACCESO",
    )


    ip = models.GenericIPAddressField(null=True, blank=True)


    dispositivo = models.ForeignKey(
        "seguridad.Dispositivo",
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
    )

    user_agent = models.CharField(max_length=400, blank=True)

    inicio = models.DateTimeField(auto_now_add=True)

    # Se escribe en cada RENOVACIÓN, no en cada petición: así cuesta una
    # escritura cada ~15 minutos y no una por request.
    ultima_actividad = models.DateTimeField(auto_now_add=True)


    fin = models.DateTimeField(null=True, blank=True)


    refresh_jti = models.CharField(max_length=32, blank=True, db_index=True)

    estado = models.ForeignKey(
        "tipologias.Tipologia",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="AGRUPADOR.ESTADO_REGISTRO — soft delete, nunca se borra.",
    )

    class Meta:
        db_table = "segu_sesion_acceso"
        verbose_name = "Acceso"
        verbose_name_plural = "Accesos"
        ordering = ["-inicio"]
        indexes = [

            models.Index(
                fields=["usuario_empresa", "fin"], name="sesion_membresia_abierta_idx"
            ),
        ]

    @property
    def esta_vencida(self) -> bool:
        """Se venció sola, por no usarla.

        Es un cálculo y no una columna: una sesión se vence con el paso del
        reloj, sin que nadie escriba nada. Si fuera columna, alguien tendría
        que ir a actualizarla — que es justo el problema de `fin`.
        """
        limite = datetime.datetime.now(datetime.UTC) - settings.SESSION_IDLE_TIMEOUT
        return self.ultima_actividad < limite

    @property
    def esta_abierta(self) -> bool:
        """ `fin` vacío NO alcanza: eso solo significa que nadie la cerró a
        mano, y casi nadie cierra sesión — cierra el navegador y se va."""
        return self.fin is None and not self.esta_vencida

    def __str__(self):
        estado = "abierta" if self.esta_abierta else f"cerrada {self.fin}"
        return f"{self.usuario_empresa} {self.inicio:%Y-%m-%d %H:%M} ({estado})"
