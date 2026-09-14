"""Abre una sucursal de un cliente, con su encargado adentro.

Lo corre el proveedor: el cliente no crea sucursales. El NIT, el rubro, el
idioma, el país y la moneda se heredan de la empresa padre.
"""

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from comun.empresas.services.empresa import (
    NOMBRE_TIPO_MATRIZ,
    NOMBRE_TIPO_SUCURSAL,
)
from comun.geografia import api as geografia
from comun.monedas import api as monedas
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR
from procesos import alta_de_sucursal
from procesos.alta_de_cliente import NOMBRE_DEL_ROL_INICIAL


class Command(BaseCommand):
    help = "Abre una sucursal de un cliente, con su encargado."

    def add_arguments(self, parser):
        parser.add_argument("--padre", required=True, type=int, help="Id de la empresa de la que cuelga.")
        parser.add_argument("--razon-social", required=True)
        parser.add_argument(
            "--encargado",
            required=True,
            help="Nombre de usuario de quien queda a cargo. Tiene que existir.",
        )
        parser.add_argument("--tipo", default=NOMBRE_TIPO_SUCURSAL, help="SUCURSAL o FILIAL.")
        parser.add_argument("--rol", default=NOMBRE_DEL_ROL_INICIAL)
        parser.add_argument("--nombre-comercial", default="")
        parser.add_argument("--pais", default="", help="Su código. Por defecto, el del padre.")
        parser.add_argument("--moneda", default="", help="Su código. Por defecto, la del padre.")

    def handle(self, *args, **opciones):
        datos = alta_de_sucursal.DatosDeLaSucursal(
            padre_id=opciones["padre"],
            razon_social=opciones["razon_social"],
            nombre_comercial=opciones["nombre_comercial"],
            tipo_empresa_id=self._tipo(opciones["tipo"]).pk,
            encargado_username=opciones["encargado"],
            rol=opciones["rol"],
            pais_id=self._pais(opciones["pais"]),
            moneda_oficial_id=self._moneda(opciones["moneda"]),
        )

        try:
            creada = alta_de_sucursal.dar_de_alta(datos)
        except ValidationError as error:
            raise CommandError("; ".join(error.messages)) from error

        self._contar(creada)

    def _tipo(self, nombre):
        fila = tipologias.obtener_del_sistema(AGRUPADOR.TIPO_EMPRESA, nombre)
        if fila is None:
            disponibles = ", ".join(
                t.nombre for t in tipologias.de(AGRUPADOR.TIPO_EMPRESA)
            )
            raise CommandError(
                f"No existe el tipo '{nombre}'. Los que hay: {disponibles}."
            )
        if fila.nombre == NOMBRE_TIPO_MATRIZ:
            raise CommandError(
                "Una casa matriz es un cliente nuevo, no una sucursal. Use "
                "crear_cliente."
            )
        return fila

    def _pais(self, codigo):
        if not codigo:
            return None
        fila = geografia.obtener_pais_por_codigo(codigo)
        if fila is None:
            raise CommandError(f"No existe el país '{codigo}'.")
        return fila.pk

    def _moneda(self, codigo):
        if not codigo:
            return None
        fila = monedas.obtener_por_codigo(codigo)
        if fila is None:
            raise CommandError(f"No existe la moneda '{codigo}'.")
        return fila.pk

    def _contar(self, creada) -> None:
        empresa = creada.empresa
        self.stdout.write(
            self.style.SUCCESS(
                f"Sucursal creada: {empresa.razon_social} (id {empresa.pk})"
            )
        )
        self.stdout.write(f"  Cuelga de: {empresa.empresa_padre_id}")
        self.stdout.write(
            f"  Encargado: {creada.encargado.username}, como {creada.rol.nombre}"
        )
