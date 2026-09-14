"""Da de alta un cliente. Lo corre el proveedor, que no tiene sesión en el ERP.

No recibe ni un id: los nombres y códigos son estables entre bases y los ids no,
así que `--rubro 7` obligaría a averiguar el 7 en cada una.
"""

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from comun.geografia import api as geografia
from comun.idiomas import api as idiomas
from comun.monedas import api as monedas
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR
from comun.usuarios import api as usuarios
from procesos import alta_de_cliente

IDIOMA_POR_DEFECTO = "es"


class Command(BaseCommand):
    help = "Da de alta un cliente con su primer administrador."

    def add_arguments(self, parser):
        parser.add_argument("--nit", required=True)
        parser.add_argument("--razon-social", required=True)
        parser.add_argument("--rubro", required=True, help="El nombre, no el id.")
        parser.add_argument("--pais", required=True, help="Su código: BO, PE.")
        parser.add_argument("--moneda", required=True, help="Su código: BOB, USD.")
        parser.add_argument("--admin-email", required=True)
        parser.add_argument("--admin-nombre", default="")
        parser.add_argument("--admin-apellido", default="")
        parser.add_argument("--admin-seg-apellido", default="")
        parser.add_argument("--admin-usuario", default="")
        parser.add_argument("--nombre-comercial", default="")
        parser.add_argument("--idioma", default=IDIOMA_POR_DEFECTO)

    def handle(self, *args, **opciones):
        cliente = alta_de_cliente.DatosDelCliente(
            ident_tributaria=opciones["nit"],
            razon_social=opciones["razon_social"],
            nombre_comercial=opciones["nombre_comercial"],
            rubro_id=self._rubro(opciones["rubro"]).pk,
            pais_id=self._pais(opciones["pais"]).pk,
            moneda_oficial_id=self._moneda(opciones["moneda"]).pk,
            idioma_default_id=self._idioma(opciones["idioma"]).pk,
        )
        administrador = alta_de_cliente.DatosDelAdministrador(
            username=self._usuario(opciones),
            email=opciones["admin_email"],
            first_name=opciones["admin_nombre"],
            last_name=opciones["admin_apellido"],
            seg_apellido=opciones["admin_seg_apellido"],
        )

        try:
            creado = alta_de_cliente.dar_de_alta(
                cliente=cliente, administrador=administrador
            )
        except ValidationError as error:
            raise CommandError("; ".join(error.messages)) from error

        self._contar(creado)

    def _rubro(self, nombre):
        fila = tipologias.obtener_del_sistema(AGRUPADOR.RUBRO, nombre)
        if fila is None:
            disponibles = ", ".join(
                t.nombre for t in tipologias.de(AGRUPADOR.RUBRO)
            )
            raise CommandError(
                f"No existe el rubro '{nombre}'. Los que hay: {disponibles or 'ninguno'}."
            )
        return fila

    def _pais(self, codigo):
        fila = geografia.obtener_pais_por_codigo(codigo)
        if fila is None:
            disponibles = ", ".join(p.cod_pais for p in geografia.listar_paises())
            raise CommandError(
                f"No existe el país '{codigo}'. Los que hay: {disponibles or 'ninguno'}."
            )
        return fila

    def _moneda(self, codigo):
        fila = monedas.obtener_por_codigo(codigo)
        if fila is None:
            raise CommandError(f"No existe la moneda '{codigo}'.")
        return fila

    def _idioma(self, codigo):
        fila = idiomas.obtener_por_codigo(codigo)
        if fila is None:
            raise CommandError(f"No existe el idioma '{codigo}'.")
        return fila

    def _usuario(self, opciones) -> str:
        """El que le pasaron, o uno armado con el nombre.

        El nombre de usuario es único en TODO el sistema, así que puede estar
        tomado por alguien de otro cliente. Se avisa en vez de inventar una
        variante: quien da de alta tiene que saber con qué nombre va a entrar
        esa persona."""
        propuesto = opciones["admin_usuario"].strip()
        if not propuesto:
            partes = [opciones["admin_nombre"], opciones["admin_apellido"]]
            propuesto = ".".join(p.strip() for p in partes if p.strip()).lower()

        if not propuesto:
            raise CommandError(
                "Falta el nombre de usuario del administrador: pase "
                "--admin-usuario, o --admin-nombre y --admin-apellido."
            )

        if usuarios.obtener_por_username(propuesto) is not None:
            raise CommandError(
                f"El nombre de usuario '{propuesto}' ya está tomado. Elija otro "
                f"con --admin-usuario."
            )
        return propuesto

    def _contar(self, creado) -> None:
        """Se imprime DESPUÉS de que la transacción confirmó. Adentro sería
        entregar la contraseña de un cliente que todavía puede no existir."""
        empresa = creado.empresa
        self.stdout.write(
            self.style.SUCCESS(
                f"Cliente creado: {empresa.razon_social} (id {empresa.pk})"
            )
        )
        self.stdout.write(f"  Rol: {creado.rol.nombre}")
        self.stdout.write(f"  Administrador: {creado.administrador.username}")
        self.stdout.write(
            self.style.WARNING(
                f"  Contraseña temporal: {creado.password_temporal}"
            )
        )
        self.stdout.write(
            "  Se muestra UNA sola vez y hay que cambiarla en el primer ingreso."
        )
