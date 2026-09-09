"""
Semilla de `pais`.

Depende de las tipologías: `Pais.estado` apunta al "Activo" del
agrupador ESTADO_REGISTRO.

A diferencia de idiomas y monedas, esta NO bloquea crear una empresa
(`Empresa.ubicacion_geografica` es nullable). Hace falta para el paso
siguiente: `Empresa_Pais` y `Ubicacion_Geografica` sí exigen un país.

NO se siembran las ubicaciones geográficas (departamentos, provincias,
municipios): son cientos de filas, no traban nada y se cargan aparte
cuando haga falta.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from comun.geografia.models import Pais
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_ACTIVO
from core.tenancy import sin_filtro_de_empresa

# (cod_pais, nombre, codigo_iso alpha-3)
PAISES = [
    ("BO", "Bolivia", "BOL"),
]


class Command(BaseCommand):
    help = "Carga los países del sistema. Idempotente."

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

            nuevos = 0
            for cod_pais, nombre, codigo_iso in PAISES:
                _, creado = Pais.objects.get_or_create(
                    codigo_iso=codigo_iso,
                    defaults={
                        "cod_pais": cod_pais,
                        "nombre": nombre,
                        "estado": activo,
                    },
                )
                nuevos += creado

        self.stdout.write(
            self.style.SUCCESS(
                f"países: {len(PAISES)} esperados, {nuevos} creados, "
                f"{len(PAISES) - nuevos} ya estaban."
            )
        )
