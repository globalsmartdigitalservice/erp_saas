"""
Acceso a datos de `Entidad`.

 TODO LO DE ACÁ YA VIENE FILTRADO POR EMPRESA. `Entidad` hereda de
`ModeloTenant`, así que su `.objects` agrega solo el `WHERE empresa_id`.
Ese es exactamente el motivo por el que resolver una FK del cliente
contra estas funciones —y no por id crudo— cierra la fuga entre empresas: un id
de otra empresa no aparece, no da "prohibido", simplemente no existe.
"""

from core.paginacion import Pagina, paginar
from dominios.entidades.models import Entidad

# EL ORDEN DE LA PAGINACIÓN, Y TERMINA EN `pk` A PROPÓSITO.
#
# Sin un orden fijo, Postgres devuelve las filas como se le canta y la
# misma entidad puede salir en la página 1 y en la 2 mientras otra no sale
# nunca. No da error: solo faltan clientes.
#
# Y el `pk` al final tampoco sobra: dos personas que se llamen igual se
# seguirían turnando entre páginas. El id desempata.
ORDEN = ["nombre", "pri_apellido", "pk"]


def obtener(entidad_id: int) -> Entidad | None:
    return Entidad.objects.filter(pk=entidad_id).first()


def obtener_varias(entidad_ids) -> dict[int, Entidad]:
    return {e.pk: e for e in Entidad.objects.filter(pk__in=list(entidad_ids))}


def listar(*, limite: int | None = None, desde: int = 0) -> Pagina:
    """
    Las entidades de la empresa activa, DE A PÁGINAS.

    Nunca devolvió y nunca va a devolver la tabla entera: un cliente con
    20.000 clientes cargados tumbaría la pantalla, y el navegador se
    bajaría 20.000 filas para mostrar 25.

    El orden y el tope no se deciden acá: son `ORDEN` y lo que impone
    `core/paginacion.py`, iguales para todo el ERP.
    """
    return paginar(Entidad.objects.all(), orden=ORDEN, limite=limite, desde=desde)


def buscar_por_documento(documento: str) -> Entidad | None:
    """
    El documento vacío NO se busca: hay muchas entidades sin documento
    cargado y todas empatarían entre sí. Devolver "la primera" sería
    peor que no encontrar nada.
    """
    if not documento:
        return None
    return Entidad.objects.filter(documento=documento).first()


def existe_documento(documento: str, excluir_id: int | None = None) -> bool:
    if not documento:
        return False
    qs = Entidad.objects.filter(documento=documento)
    if excluir_id is not None:
        qs = qs.exclude(pk=excluir_id)
    return qs.exists()


def crear(**campos) -> Entidad:
    # `empresa` no se pasa: la pone `ModeloTenant.save()` desde el
    # contexto de la petición.
    return Entidad.objects.create(**campos)


def actualizar(entidad: Entidad, **campos) -> Entidad:
    for campo, valor in campos.items():
        setattr(entidad, campo, valor)
    entidad.save(update_fields=list(campos))
    return entidad
