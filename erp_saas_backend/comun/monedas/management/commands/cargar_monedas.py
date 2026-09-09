"""
Semilla de `moneda`.

Depende de las tipologías: `Moneda.estado` apunta al "Activo" del
agrupador ESTADO_REGISTRO. Si no están cargadas, revienta con un mensaje
que dice qué correr — no deja la base a medias.

Hace falta porque el alta de una empresa exige decir su moneda base,
y esa moneda tiene que existir en el catálogo antes.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from comun.monedas.models import Moneda
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_ACTIVO
from core.tenancy import sin_filtro_de_empresa


MONEDAS = [
    ("BOB", "Boliviano", "Bs"),
    ("USD", "Dólar estadounidense", "$"),
]


class Command(BaseCommand):
    help = "Carga las monedas del sistema. Idempotente."

    @transaction.atomic
    def handle(self, *args, **options):
        with sin_filtro_de_empresa():

            activo = tipologias.obtener_del_sistema(
                AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_ACTIVO
            )
            if activo is None:
                raise CommandError(
                    f"Falta la tipología '{NOMBRE_ESTADO_ACTIVO}' del agrupador "
                    f"ESTADO_REGISTRO. Ejecute primero: "
                    f"python manage.py cargar_tipologias"
                )

            nuevas = 0
            for codigo, descripcion, simbolo in MONEDAS:
                _, creada = Moneda.objects.get_or_create(
                    codigo=codigo,
                    defaults={
                        "descripcion": descripcion,
                        "simbolo": simbolo,
                        "estado": activo,
                    },
                )
                nuevas += creada

        self.stdout.write(
            self.style.SUCCESS(
                f"monedas: {len(MONEDAS)} esperadas, {nuevas} creadas, "
                f"{len(MONEDAS) - nuevas} ya estaban."
            )
        )
