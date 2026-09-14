"""El alta de una sucursal: la empresa y su encargado, juntos.

Lo corre el proveedor —la ingeniera decidió que el cliente no crea sucursales—
y el encargado es obligatorio: es lo único que impide que una sucursal nazca sin
nadie adentro, que sería imposible de poblar después.
"""

import dataclasses

from django.core.exceptions import ValidationError
from django.db import transaction

from comun.empresas import api as empresas
from comun.empresas.services.empresa import NOMBRE_ESTADO_ACTIVA
from comun.membresias import api as membresias
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_ACTIVO
from comun.usuarios import api as usuarios
from core.tenancy import empresa as contexto_empresa
from dominios.seguridad import api as seguridad
from procesos.alta_de_cliente import NOMBRE_DEL_ROL_INICIAL


@dataclasses.dataclass(frozen=True)
class DatosDeLaSucursal:
    padre_id: int
    razon_social: str
    tipo_empresa_id: int
    encargado_username: str
    nombre_comercial: str = ""
    rol: str = NOMBRE_DEL_ROL_INICIAL
    pais_id: int | None = None
    moneda_oficial_id: int | None = None


class SucursalNueva:
    def __init__(self, *, empresa, encargado, membresia, rol):
        self.empresa = empresa
        self.encargado = encargado
        self.membresia = membresia
        self.rol = rol


def _padre_o_fallar(padre_id: int):
    padre = empresas.obtener_empresa(padre_id)
    if padre is None:
        raise ValidationError(f"No existe la empresa {padre_id}.")
    return padre


def _heredado(padre, datos: DatosDeLaSucursal) -> dict:
    """País y moneda salen de la empresa padre salvo que se pidan otros.

    Se pueden pedir otros porque una sucursal en otro país es una entidad legal
    de ese país y lleva sus libros en su moneda."""
    pais_id = datos.pais_id
    if pais_id is None:
        fichas = empresas.listar_paises_de(padre.pk)
        if not fichas:
            raise ValidationError(
                f"La empresa {padre.pk} no tiene país cargado, así que no se "
                f"sabe cuál heredarle a la sucursal."
            )
        pais_id = fichas[0].pais_id

    moneda_id = datos.moneda_oficial_id
    if moneda_id is None:
        moneda = empresas.moneda_oficial_de(padre.pk)
        if moneda is None:
            raise ValidationError(
                f"La empresa {padre.pk} no tiene moneda oficial, así que no se "
                f"sabe cuál heredarle a la sucursal."
            )
        moneda_id = moneda.pk

    return {"pais_id": pais_id, "moneda_oficial_id": moneda_id}


def _encargado_del_cliente(username: str, matriz_id: int):
    """La persona que va a quedar a cargo, si es de ese cliente."""
    persona = usuarios.obtener_por_username(username)
    if persona is None or persona.matriz_id != matriz_id:
        raise ValidationError(
            f"'{username}' no es una persona de ese cliente. El encargado tiene "
            f"que estar dado de alta antes de abrir la sucursal."
        )
    return persona


def _rol_asignable(nombre: str):
    """Los roles se ven por ámbito, así que en una sucursal recién creada solo
    sirven los de la matriz. Es donde el alta de cliente deja el suyo."""
    rol = next((r for r in seguridad.listar_roles() if r.nombre == nombre), None)
    if rol is None:
        disponibles = ", ".join(r.nombre for r in seguridad.listar_roles())
        raise ValidationError(
            f"No existe el rol '{nombre}' en la casa matriz de ese cliente. "
            f"Los que hay: {disponibles or 'ninguno'}."
        )
    return rol


def _tipologia(agrupador: int, nombre: str):
    fila = tipologias.obtener_del_sistema(agrupador, nombre)
    if fila is None:
        raise ValidationError(
            f"Falta la tipología '{nombre}'. Ejecute: python manage.py cargar_semillas"
        )
    return fila


@transaction.atomic
def dar_de_alta(datos: DatosDeLaSucursal) -> SucursalNueva:
    """Crea la sucursal con su encargado adentro. O entra todo, o no entra nada.

    El NIT no se pide: una sucursal comparte el de su matriz, y `crear_empresa`
    ya lo contempla."""
    padre = _padre_o_fallar(datos.padre_id)
    matriz = empresas.matriz_de(padre.pk)

    encargado = _encargado_del_cliente(datos.encargado_username, matriz.pk)

    sucursal = empresas.crear_empresa(
        ident_tributaria=padre.ident_tributaria,
        razon_social=datos.razon_social,
        nombre_comercial=datos.nombre_comercial,
        tipo_empresa_id=datos.tipo_empresa_id,
        rubro_id=padre.rubro_id,
        estado_id=_tipologia(AGRUPADOR.ESTADO_EMPRESA, NOMBRE_ESTADO_ACTIVA).pk,
        idioma_default_id=padre.idioma_default_id,
        empresa_padre_id=padre.pk,
        **_heredado(padre, datos),
    )

    activo = _tipologia(AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_ACTIVO)

    with contexto_empresa(sucursal.pk):
        rol = _rol_asignable(datos.rol)
        membresia = membresias.afiliar(
            usuario_id=encargado.pk, estado_id=activo.pk
        )
        seguridad.asignar_rol(
            membresia_id=membresia.pk, grupo_id=rol.pk, estado_id=activo.pk
        )

    return SucursalNueva(
        empresa=sucursal, encargado=encargado, membresia=membresia, rol=rol
    )


__all__ = ["dar_de_alta", "DatosDeLaSucursal", "SucursalNueva"]
