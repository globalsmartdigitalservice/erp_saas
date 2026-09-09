"""Acceso a datos de `Sub_Modulo`. Sin filtro de empresa: catálogo del
proveedor. Cada listado trae su `select_related` porque esto arma EL MENÚ:
sin él son 40 consultas extra por carga de pantalla."""


from comun.catalogo_modulos.models import SubModulo


def obtener(sub_modulo_id: int) -> SubModulo | None:
    return SubModulo.objects.filter(pk=sub_modulo_id).first()


def obtener_varios(sub_modulo_ids) -> dict[int, SubModulo]:
    return {
        s.pk: s
        for s in SubModulo.objects.select_related("modulo_sistema").filter(
            pk__in=list(sub_modulo_ids)
        )
    }


def obtener_por_codigo(codigo: str) -> SubModulo | None:
    """
    Por el código estable. Es el camino del generador de permisos: el
    `recurso` que escanea de las mutations se busca acá.
    """
    return SubModulo.objects.select_related("modulo_sistema").filter(
        codigo=codigo
    ).first()


def listar(estado_id: int | None = None) -> list[SubModulo]:
    qs = SubModulo.objects.select_related("modulo_sistema")
    if estado_id is not None:
        qs = qs.filter(estado_id=estado_id)
    return list(qs)


def listar_de_modulo(modulo_id: int, estado_id: int | None = None) -> list[SubModulo]:
    """Las pantallas de UN módulo."""
    qs = SubModulo.objects.select_related("modulo_sistema").filter(
        modulo_sistema_id=modulo_id
    )
    if estado_id is not None:
        qs = qs.filter(estado_id=estado_id)
    return list(qs)


def listar_de_modulos(modulo_ids, estado_id: int | None = None) -> list[SubModulo]:
    """
    Las pantallas de VARIOS módulos, en UNA consulta.

    Es la que arma el menú: el sistema sabe qué módulos tiene contratado
    el cliente y pide las pantallas de todos juntos. Sin esta, el menú
    hace una consulta por módulo contratado.
    """
    qs = SubModulo.objects.select_related("modulo_sistema").filter(
        modulo_sistema_id__in=list(modulo_ids)
    )
    if estado_id is not None:
        qs = qs.filter(estado_id=estado_id)
    return list(qs)


def existe_codigo(codigo: str, excluir_id: int | None = None) -> bool:
    qs = SubModulo.objects.filter(codigo=codigo)
    if excluir_id is not None:
        qs = qs.exclude(pk=excluir_id)
    return qs.exists()


def existe_ruta(ruta: str, excluir_id: int | None = None) -> bool:
    qs = SubModulo.objects.filter(ruta=ruta)
    if excluir_id is not None:
        qs = qs.exclude(pk=excluir_id)
    return qs.exists()


def existe_nombre_en_modulo(
    modulo_id: int, nombre: str, excluir_id: int | None = None
) -> bool:
    qs = SubModulo.objects.filter(modulo_sistema_id=modulo_id, nombre=nombre)
    if excluir_id is not None:
        qs = qs.exclude(pk=excluir_id)
    return qs.exists()


def tiene_funcionalidades(sub_modulo_id: int) -> bool:
    """Para la baja: una pantalla con acciones vivas no se desactiva sola."""
    return SubModulo.objects.filter(
        pk=sub_modulo_id, funcionalidades__isnull=False
    ).exists()


def crear(**campos) -> SubModulo:
    return SubModulo.objects.create(**campos)


def actualizar(sub_modulo: SubModulo, **campos) -> SubModulo:
    for campo, valor in campos.items():
        setattr(sub_modulo, campo, valor)
    sub_modulo.save(update_fields=list(campos))
    return sub_modulo
