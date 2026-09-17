"""Deja la base lista para entrar al frontend sin pasar por el login.

    python manage.py preparar_dev

Se borra junto con `crear_cliente` cuando exista el panel del proveedor.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from comun.geografia import api as geografia
from comun.idiomas import api as idiomas
from comun.monedas import api as monedas
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR
from comun.usuarios import api as usuarios
from procesos import alta_de_cliente

NIT = "1000001"
RAZON_SOCIAL = "Salon de Belleza Sofia"
RUBRO = "SERVICIOS"
PAIS = "BO"
MONEDA = "BOB"
IDIOMA = "es"

USUARIO = "dev"
EMAIL = "dev@erp.local"
NOMBRE = "Dev"
PASSWORD = "Dev2026**"


class Command(BaseCommand):
    help = "Deja la base lista para entrar al frontend sin pasar por el login."

    def handle(self, *args, **opciones):
        if not settings.DEBUG:
            raise CommandError(
                "Solo corre en desarrollo: crea una cuenta con una contraseña "
                "que está escrita en el código."
            )

        if usuarios.obtener_por_username(USUARIO) is not None:
            self.stdout.write(f"'{USUARIO}' ya existe: no se toca nada.")
            self._imprimir_credenciales()
            return

        try:
            creado = self._dar_de_alta()
        except ValidationError as error:
            raise CommandError("; ".join(error.messages)) from error

        self.stdout.write(
            self.style.SUCCESS(
                f"Listo: {creado.empresa.razon_social} (id {creado.empresa.pk})"
            )
        )
        self._imprimir_credenciales()

    @transaction.atomic
    def _dar_de_alta(self):
        creado = alta_de_cliente.dar_de_alta(
            cliente=self._cliente(),
            administrador=alta_de_cliente.DatosDelAdministrador(
                username=USUARIO, email=EMAIL, first_name=NOMBRE
            ),
            password=PASSWORD,
        )

        cuenta = creado.administrador
        cuenta.debe_cambiar_password = False
        cuenta.save(update_fields=["debe_cambiar_password"])
        return creado

    def _cliente(self):
        return alta_de_cliente.DatosDelCliente(
            ident_tributaria=NIT,
            razon_social=RAZON_SOCIAL,
            rubro_id=self._exigir(
                tipologias.obtener_del_sistema(AGRUPADOR.RUBRO, RUBRO), RUBRO
            ).pk,
            pais_id=self._exigir(
                geografia.obtener_pais_por_codigo(PAIS), PAIS
            ).pk,
            moneda_oficial_id=self._exigir(
                monedas.obtener_por_codigo(MONEDA), MONEDA
            ).pk,
            idioma_default_id=self._exigir(
                idiomas.obtener_por_codigo(IDIOMA), IDIOMA
            ).pk,
        )

    def _exigir(self, fila, nombre: str):
        if fila is None:
            raise CommandError(
                f"Falta '{nombre}'. Ejecute: python manage.py cargar_semillas"
            )
        return fila

    def _imprimir_credenciales(self):
        self.stdout.write("\nEntre al frontend con:\n")
        self.stdout.write(f"  Usuario:    {USUARIO}")
        self.stdout.write(f"  Contraseña: {PASSWORD}")
