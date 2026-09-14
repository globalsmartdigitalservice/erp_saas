"""
Superficie pública de `geografia`. El resto de la app es privado.

Nadie de afuera importa `models`, `repository` ni `services`. Se puede
reescribir el interior entero — mientras estas firmas respondan igual,
los consumidores ni se enteran.

Uso:

    from comun.geografia import api as geografia

    paises = geografia.listar_paises()

REGLA DEL LOTE
    Todo `obtener_x(id)` viene acompañado de `obtener_varios_x(ids)`.
    No es una buena práctica: es parte del contrato de la capa. Sin la
    versión por lote, cada resolver que cruce esta frontera reintroduce
    el N+1.

Las lecturas van directo al repository (no hay nada que decidir); las
escrituras pasan siempre por services, que es donde están los invariantes.
"""

from comun.geografia.models import Pais, UbicacionGeografica
from comun.geografia.repository import pais as _repo_pais
from comun.geografia.repository import ubicacion as _repo_ubicacion
from comun.geografia.services import pais as _svc_pais
from comun.geografia.services import ubicacion as _svc_ubicacion


def obtener_pais(pais_id: int) -> Pais | None:
    return _repo_pais.obtener(pais_id)


def obtener_paises(pais_ids) -> dict[int, Pais]:
    return _repo_pais.obtener_varios(pais_ids)


def obtener_pais_por_codigo(cod_pais: str) -> Pais | None:
    """Por su código corto (`BO`), como en monedas e idiomas. Los códigos son
    estables entre bases; los ids no, y por eso los comandos hablan en códigos."""
    return _repo_pais.obtener_por_codigo((cod_pais or "").strip().upper())


def listar_paises() -> list[Pais]:
    return _repo_pais.listar()


def crear_pais(*, cod_pais: str, nombre: str, codigo_iso: str, estado_id: int) -> Pais:
    return _svc_pais.crear(
        cod_pais=cod_pais, nombre=nombre, codigo_iso=codigo_iso, estado_id=estado_id
    )


def actualizar_pais(pais_id: int, **campos) -> Pais:
    return _svc_pais.actualizar(pais_id, **campos)


def desactivar_pais(pais_id: int) -> Pais:
    return _svc_pais.desactivar(pais_id)


def obtener_ubicacion(ubicacion_id: int) -> UbicacionGeografica | None:
    return _repo_ubicacion.obtener(ubicacion_id)


def obtener_ubicaciones(ubicacion_ids) -> dict[int, UbicacionGeografica]:
    return _repo_ubicacion.obtener_varias(ubicacion_ids)


def listar_ubicaciones_de_pais(pais_id: int) -> list[UbicacionGeografica]:
    return _repo_ubicacion.listar_de_pais(pais_id)


def listar_raices(pais_id: int) -> list[UbicacionGeografica]:
    """Las divisiones de primer nivel de un país (los departamentos)."""
    return _repo_ubicacion.listar_raices(pais_id)


def hijos_de(ubicacion_id: int) -> list[UbicacionGeografica]:
    """
    Las divisiones hijas DIRECTAS.

    Para "todos los municipios de Santa Cruz" hace falta una consulta
    recursiva (CTE). No está implementada todavía: se agrega acá cuando
    aparezca el primer caso de uso real.
    """
    return _repo_ubicacion.listar_hijas(ubicacion_id)


def crear_ubicacion(
    *,
    pais_id: int,
    nombre: str,
    tipo: str,
    estado_id: int,
    division_superior_id: int | None = None,
    codigo: str = "",
) -> UbicacionGeografica:
    return _svc_ubicacion.crear(
        pais_id=pais_id,
        nombre=nombre,
        tipo=tipo,
        estado_id=estado_id,
        division_superior_id=division_superior_id,
        codigo=codigo,
    )


def mover_ubicacion(ubicacion_id: int, nuevo_padre_id: int | None) -> UbicacionGeografica:
    return _svc_ubicacion.mover(ubicacion_id, nuevo_padre_id)


def desactivar_ubicacion(ubicacion_id: int) -> UbicacionGeografica:
    return _svc_ubicacion.desactivar(ubicacion_id)


__all__ = [
    "obtener_pais",
    "obtener_paises",
    "listar_paises",
    "crear_pais",
    "actualizar_pais",
    "desactivar_pais",
    "obtener_ubicacion",
    "obtener_ubicaciones",
    "listar_ubicaciones_de_pais",
    "listar_raices",
    "hijos_de",
    "crear_ubicacion",
    "mover_ubicacion",
    "desactivar_ubicacion",
]
