"""
Acceso a datos de `Traduccion`.

Todas las consultas salen por `Traduccion.objects`, que es el manager
con el filtro de empresa. La única excepción está marcada abajo.

 ACÁ NO SE DECIDE CUÁL TRADUCCIÓN GANA. Cuando una fila tiene
traducción propia y de fábrica, elegir es una regla de negocio y vive en
`services/traduccion.py`. Este archivo devuelve las filas que hay.
"""

from comun.idiomas.models import Traduccion


def obtener(traduccion_id: int) -> Traduccion | None:
    return Traduccion.objects.filter(pk=traduccion_id).first()


def obtener_varias(traduccion_ids) -> dict[int, Traduccion]:
    return {
        t.pk: t for t in Traduccion.objects.filter(pk__in=list(traduccion_ids))
    }


def filas_para(
    entidad_tipo: str, entidad_ids, campo: str, idioma_id: int
) -> list[Traduccion]:
    """
    LA CONSULTA DEL LOTE, que es de lo que vive este archivo.

    Trae en UNA sola consulta las traducciones de N filas. Sin esto,
    listar 400 tipologías serían 400 consultas más — exactamente el N+1
    que la arquitectura prohíbe y que el resto del proyecto ya evita con
    `obtener_varias()`.

    Puede devolver más de una fila por `entidad_id` (la propia y la de
    fábrica). Quién gana lo resuelve el service.
    """
    ids = list(entidad_ids)
    if not ids:
        return []

    return list(
        Traduccion.objects.filter(
            entidad_tipo=entidad_tipo,
            campo=campo,
            idioma_id=idioma_id,
            entidad_id__in=ids,
        )
    )


def listar_de(entidad_tipo: str, entidad_id: int) -> list[Traduccion]:
    """
    Todas las traducciones de UNA fila, en todos los idiomas y campos.

    Es lo que necesita el formulario: al editar una categoría hay que
    mostrar sus textos en cada idioma activo.
    """
    return list(
        Traduccion.objects.filter(
            entidad_tipo=entidad_tipo, entidad_id=entidad_id
        ).select_related("idioma")
    )


def buscar(
    entidad_tipo: str,
    entidad_id: int,
    campo: str,
    idioma_id: int,
    empresa_id: int | None,
) -> Traduccion | None:
    """
    La fila exacta de una empresa (o la de fábrica con `empresa_id`
    None). La usa el service para decidir si crea o actualiza.

    Va por `objects` igual que todo lo demás: si la fila fuera de otra
    empresa, el manager no la devuelve y el service crea una propia,
    que es justo lo correcto.
    """
    return Traduccion.objects.filter(
        entidad_tipo=entidad_tipo,
        entidad_id=entidad_id,
        campo=campo,
        idioma_id=idioma_id,
        empresa_id=empresa_id,
    ).first()


def crear(
    *,
    empresa_id: int | None,
    entidad_tipo: str,
    entidad_id: int,
    campo: str,
    idioma_id: int,
    texto: str,
) -> Traduccion:
    return Traduccion.objects.create(
        empresa_id=empresa_id,
        entidad_tipo=entidad_tipo,
        entidad_id=entidad_id,
        campo=campo,
        idioma_id=idioma_id,
        texto=texto,
    )


def actualizar(traduccion: Traduccion, **campos) -> Traduccion:
    for campo, valor in campos.items():
        setattr(traduccion, campo, valor)
    traduccion.save(update_fields=list(campos))
    return traduccion


def borrar(traduccion: Traduccion) -> None:
    """
    BORRADO FÍSICO, y es a propósito.

    En este ERP nada se borra… pero una traducción no es un dato: es la
    misma información en otro idioma. Sacarla no pierde nada —el texto
    original sigue en su tabla— y un soft delete acá obligaría a que
    cada lectura filtre por estado. El modelo de datos tampoco le da
    `estadoId` a esta tabla.
    """
    traduccion.delete()
