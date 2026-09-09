"""Superficie pública de `entidades`. El resto de la app es privado.

    from dominios.entidades import api as entidades

    cliente = entidades.crear_entidad(...)

 La versión por lote pesa más acá que en ningún otro módulo: una lista
de entidades resuelve roles, direcciones y contactos de cada fila, así que
sin ella cada resolver que cruce esta frontera reintroduce el N+1.

 NINGUNA FUNCIÓN RECIBE `empresa_id`, Y NO ES UN OLVIDO. La empresa sale
del contexto de la petición, nunca de lo que manda el cliente. Si alguna
vez alguien necesita agregar ese parámetro, la respuesta casi seguro es
que está resolviendo el problema equivocado.

Las lecturas van directo al repository; las escrituras pasan por services,
que es donde están los invariantes.
"""

from core.paginacion import Pagina
from dominios.entidades.models import (
    CategoriaEntidad,
    ContactoEntidad,
    Direccion,
    EncuestaSatisfaccion,
    Entidad,
    RolEntidad,
)
from dominios.entidades.repository import categoria_entidad as _repo_categoria
from dominios.entidades.repository import contacto_entidad as _repo_contacto
from dominios.entidades.repository import direccion as _repo_direccion
from dominios.entidades.repository import encuesta_satisfaccion as _repo_encuesta
from dominios.entidades.repository import entidad as _repo_entidad
from dominios.entidades.repository import rol_entidad as _repo_rol
from dominios.entidades.services import categoria_entidad as _svc_categoria
from dominios.entidades.services import contacto_entidad as _svc_contacto
from dominios.entidades.services import direccion as _svc_direccion
from dominios.entidades.services import encuesta_satisfaccion as _svc_encuesta
from dominios.entidades.services import entidad as _svc_entidad
from dominios.entidades.services import rol_entidad as _svc_rol


def obtener_entidad(entidad_id: int) -> Entidad | None:
    return _repo_entidad.obtener(entidad_id)


def obtener_entidades(entidad_ids) -> dict[int, Entidad]:
    return _repo_entidad.obtener_varias(entidad_ids)


def listar_entidades(*, limite: int | None = None, desde: int = 0) -> Pagina:
    """
    Las entidades de la empresa activa, DE A PÁGINAS.

    Devuelve una `Pagina` (`items` + `total`), no una lista: sin el total
    la pantalla no puede decir "página 3 de 20" ni saber si hay más.

    Por defecto trae 25 y el tope es 100. Más allá de 10.000 registros se
    corta y se pide filtrar — ver `core/paginacion.py`.
    """
    return _repo_entidad.listar(limite=limite, desde=desde)


def buscar_entidad_por_documento(documento: str) -> Entidad | None:
    """El documento vacío no se busca: todas las que no lo tienen empatarían."""
    return _repo_entidad.buscar_por_documento(documento)


def crear_entidad(**campos) -> Entidad:
    return _svc_entidad.crear(**campos)


def actualizar_entidad(entidad_id: int, **campos) -> Entidad:
    return _svc_entidad.actualizar(entidad_id, **campos)


def desactivar_entidad(entidad_id: int) -> Entidad:
    return _svc_entidad.desactivar(entidad_id)


def obtener_categoria(categoria_id: int) -> CategoriaEntidad | None:
    return _repo_categoria.obtener(categoria_id)


def obtener_categorias(categoria_ids) -> dict[int, CategoriaEntidad]:
    return _repo_categoria.obtener_varias(categoria_ids)


def listar_categorias() -> list[CategoriaEntidad]:
    return _repo_categoria.listar()


def crear_categoria(**campos) -> CategoriaEntidad:
    return _svc_categoria.crear(**campos)


def actualizar_categoria(categoria_id: int, **campos) -> CategoriaEntidad:
    return _svc_categoria.actualizar(categoria_id, **campos)


def desactivar_categoria(categoria_id: int) -> CategoriaEntidad:
    return _svc_categoria.desactivar(categoria_id)


def obtener_rol(rol_id: int) -> RolEntidad | None:
    return _repo_rol.obtener(rol_id)


def obtener_roles(rol_ids) -> dict[int, RolEntidad]:
    return _repo_rol.obtener_varios(rol_ids)


def listar_roles_de(entidad_id: int) -> list[RolEntidad]:
    return _repo_rol.listar_de(entidad_id)


def listar_por_tipo_de_rol(tipo_rol_id: int) -> list[RolEntidad]:
    """Los clientes, o los proveedores: la consulta que hace el negocio."""
    return _repo_rol.listar_por_tipo(tipo_rol_id)


def crear_rol(**campos) -> RolEntidad:
    return _svc_rol.crear(**campos)


def actualizar_rol(rol_id: int, **campos) -> RolEntidad:
    return _svc_rol.actualizar(rol_id, **campos)


def desactivar_rol(rol_id: int) -> RolEntidad:
    return _svc_rol.desactivar(rol_id)


def obtener_direccion(direccion_id: int) -> Direccion | None:
    return _repo_direccion.obtener(direccion_id)


def obtener_direcciones(direccion_ids) -> dict[int, Direccion]:
    return _repo_direccion.obtener_varias(direccion_ids)


def listar_direcciones_de(entidad_id: int) -> list[Direccion]:
    return _repo_direccion.listar_de(entidad_id)


def crear_direccion(**campos) -> Direccion:
    return _svc_direccion.crear(**campos)


def actualizar_direccion(direccion_id: int, **campos) -> Direccion:
    return _svc_direccion.actualizar(direccion_id, **campos)


def desactivar_direccion(direccion_id: int) -> Direccion:
    return _svc_direccion.desactivar(direccion_id)


def obtener_contacto(contacto_id: int) -> ContactoEntidad | None:
    return _repo_contacto.obtener(contacto_id)


def obtener_contactos(contacto_ids) -> dict[int, ContactoEntidad]:
    return _repo_contacto.obtener_varios(contacto_ids)


def listar_contactos_de(entidad_id: int) -> list[ContactoEntidad]:
    return _repo_contacto.listar_de(entidad_id)


def crear_contacto(**campos) -> ContactoEntidad:
    return _svc_contacto.crear(**campos)


def actualizar_contacto(contacto_id: int, **campos) -> ContactoEntidad:
    return _svc_contacto.actualizar(contacto_id, **campos)


def desactivar_contacto(contacto_id: int) -> ContactoEntidad:
    return _svc_contacto.desactivar(contacto_id)


def obtener_encuesta(encuesta_id: int) -> EncuestaSatisfaccion | None:
    return _repo_encuesta.obtener(encuesta_id)


def obtener_encuestas(encuesta_ids) -> dict[int, EncuestaSatisfaccion]:
    return _repo_encuesta.obtener_varias(encuesta_ids)


def listar_encuestas_de(entidad_id: int) -> list[EncuestaSatisfaccion]:
    return _repo_encuesta.listar_de(entidad_id)


def registrar_encuesta(**campos) -> EncuestaSatisfaccion:
    """No se llama `crear`: lo que entra es un hecho ocurrido, no un dato."""
    return _svc_encuesta.registrar(**campos)
