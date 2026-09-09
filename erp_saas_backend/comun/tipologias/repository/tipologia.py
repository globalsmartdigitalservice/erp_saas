"""Acceso a datos de `Tipologia`.

 TODO LO QUE DEVUELVE VALORES PASA POR `.valores()`. La tabla guarda el
nombre de cada lista (la cabecera, `indice = 0`) y los valores de esa
lista; una función que se olvide del filtro devuelve "Rubros" mezclado
entre los rubros. Las cabeceras se piden por `listar_cabeceras()`.

La única excepción está marcada abajo: `existe_nombre_visible`.
"""

from django.db.models import Max

from comun.tipologias.models import Tipologia


def obtener(tipologia_id: int) -> Tipologia | None:
    """
    Una tipología visible para la empresa activa: las suyas, las de su
    casa matriz y las de fábrica, menos las ocultas. Las de otra empresa
    dan None — el aislamiento lo pone el manager, no quien consulta.

    **Una cabecera tampoco se devuelve acá**, y es a propósito: así
    ninguna FK puede apuntarle ni nadie la edita creyendo que borra una
    opción. Se llega a ella por `listar_cabeceras()`.
    """
    return Tipologia.objects.valores().filter(pk=tipologia_id).first()


def obtener_incluso_cabecera(tipologia_id: int) -> Tipologia | None:
    """
    Como `obtener`, pero SIN esconder las cabeceras.

     Existe para una sola cosa —redactar el error de
    `api.exigir_del_agrupador`— y no la usa nadie más: sin poder ver la
    cabecera, el mensaje decía "no existe" para una fila que existe.

    El aislamiento no se toca: sigue yendo por el manager multiempresa,
    así que una fila de otro cliente da None y su nombre nunca se filtra.
    """
    return Tipologia.objects.filter(pk=tipologia_id).first()


def obtener_varias(ids) -> dict[int, Tipologia]:
    return {t.pk: t for t in Tipologia.objects.valores().filter(pk__in=list(ids))}


def listar_del_agrupador(agrupador: int, solo_activas: bool = True) -> list[Tipologia]:
    qs = Tipologia.objects.valores().del_agrupador(agrupador)
    if solo_activas:
        qs = qs.activas()
    return list(qs)


def obtener_del_sistema(agrupador: int, nombre: str) -> Tipologia | None:
    """
    Una fila del CATÁLOGO DEL SISTEMA por su nombre. `empresa__isnull`
    va explícito: se quiere la del sistema, no una que alguna empresa se
    haya creado con el mismo nombre.
    """
    return (
        Tipologia.objects.valores()
        .filter(empresa__isnull=True, agrupador=agrupador, nombre=nombre)
        .first()
    )


def listar_cabeceras() -> list[Tipologia]:
    """
    El nombre de cada lista, una fila por agrupador. Es la fuente del
    nombre en vez de `AGRUPADOR.choices`, así lo cambia el proveedor sin
    redesplegar. **Devuelve vacío si no se corrió `cargar_semillas`.**
    """
    return list(Tipologia.objects.cabeceras())


def obtener_cabecera(agrupador: int) -> Tipologia | None:
    return Tipologia.objects.cabeceras().del_agrupador(agrupador).first()


def siguiente_indice(agrupador: int) -> int:
    """
    El índice del próximo valor de esa lista: el último + 1.

    Se calcula sobre lo VISIBLE, así que una sucursal sigue la numeración
    de lo que heredó de su matriz en vez de pisarla.
    """
    ultimo = Tipologia.objects.del_agrupador(agrupador).aggregate(
        n=Max("indice")
    )["n"]
    return (ultimo or 0) + 1


def existe_nombre_visible(
    agrupador: int,
    nombre: str,
    excluir_id: int | None = None,
) -> bool:
    """
    ¿La empresa activa YA VE un valor con ese nombre en esa lista?

    Va contra el manager a propósito, y con eso cubre de una sola vez la
    constraint única (empresa, agrupador, nombre) y lo que la constraint
    NO puede: la matriz y la fábrica son filas de otra empresa, Postgres
    las deja pasar y el combo mostraría dos "QR". Lo que la empresa tiene
    oculto no cuenta, así que puede crearse el suyo.

    No filtra por estado: una fila desactivada sigue ocupando el nombre.

     **LA EXCEPCIÓN DEL ARCHIVO: tampoco filtra `.valores()`.** La
    cabecera es una fila más para la constraint, así que salteándola un
    rubro llamado "Rubros" pasaría la validación y moriría con un
    IntegrityError en vez de un mensaje claro.
    """
    qs = Tipologia.objects.del_agrupador(agrupador).filter(nombre=nombre)
    if excluir_id is not None:
        qs = qs.exclude(pk=excluir_id)
    return qs.exists()


def crear(
    *,
    empresa_id: int | None,
    agrupador: int,
    nombre: str,
    abreviatura: str = "",
    indice: int,
) -> Tipologia:
    return Tipologia.objects.create(
        empresa_id=empresa_id,
        agrupador=agrupador,
        nombre=nombre,
        abreviatura=abreviatura,
        indice=indice,
    )


def actualizar(tipologia: Tipologia, **campos) -> Tipologia:
    for campo, valor in campos.items():
        setattr(tipologia, campo, valor)
    tipologia.save(update_fields=list(campos))
    return tipologia
