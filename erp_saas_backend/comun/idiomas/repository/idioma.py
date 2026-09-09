"""Acceso a datos de `Idioma`."""

from comun.idiomas.models import Idioma


def obtener(idioma_id: int) -> Idioma | None:
    return Idioma.objects.filter(pk=idioma_id).first()


def obtener_varios(idioma_ids) -> dict[int, Idioma]:
    return {i.pk: i for i in Idioma.objects.filter(pk__in=list(idioma_ids))}


def listar(solo_activos: bool = False) -> list[Idioma]:
    """
    Todos los idiomas, o solo los activos.

    Acá SÍ se puede filtrar con un booleano, al revés que en `monedas`:
    `Idioma.activo` es un `BooleanField` y no una FK a `Tipologia`, así
    que "activo" es un valor que esta capa conoce sin resolver nada.
    Es la única tabla del módulo 11/13 así — el modelo de datos lo dice
    explícito ("Bandera booleana: activo").
    """
    qs = Idioma.objects.all()
    if solo_activos:
        qs = qs.filter(activo=True)
    return list(qs)


def obtener_por_codigo(codigo: str) -> Idioma | None:
    return Idioma.objects.filter(codigo=codigo).first()


def existe_codigo(codigo: str, excluir_id: int | None = None) -> bool:
    qs = Idioma.objects.filter(codigo=codigo)
    if excluir_id is not None:
        qs = qs.exclude(pk=excluir_id)
    return qs.exists()


def crear(*, codigo: str, nombre: str, activo: bool = True) -> Idioma:
    return Idioma.objects.create(codigo=codigo, nombre=nombre, activo=activo)


def actualizar(idioma: Idioma, **campos) -> Idioma:
    for campo, valor in campos.items():
        setattr(idioma, campo, valor)
    idioma.save(update_fields=list(campos))
    return idioma
