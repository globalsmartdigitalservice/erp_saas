import pytest
from django.apps import apps
from django.core.exceptions import FieldDoesNotExist



REFERENCIAS_PENDIENTES = {
    ("entidades", "CategoriaEntidad", "lista_precio_id"): (
        ("catalogo", "ListaPrecio"),
        "Módulo 05.1 (Catálogo), no construido. En el modelo de datos la línea "
        "es punteada y dice 'lista asignada [suave]', así que puede quedarse "
        "como entero a propósito. Se dejó IntegerField para no bloquear el "
        "módulo 04 con una FK sin destino. Hoy no lo lee ningún código.",
    ),
}


def _existe(app_label: str, modelo: str) -> bool:
    try:
        apps.get_model(app_label, modelo)
    except LookupError:
        return False
    return True


def test_ninguna_referencia_pendiente_tiene_ya_su_destino():
    resueltas = []

    for (app, modelo, campo), ((app_dest, modelo_dest), motivo) in (
        REFERENCIAS_PENDIENTES.items()
    ):
        if not _existe(app_dest, modelo_dest):
            continue

        resueltas.append(
            f"\n  · {app}.{modelo}.{campo}  →  ya existe {app_dest}.{modelo_dest}"
            f"\n    Se dejó así porque: {motivo}"
        )

    assert not resueltas, (
        "Estas referencias se dejaron como entero suelto porque su tabla "
        "destino no existía, y AHORA EXISTE:" + "".join(resueltas) + "\n\n"
        "Ese motivo ya no aplica. Por cada una, decidí una de dos:\n"
        "  · convertirla en FK real, con su migración\n"
        "  · dejarla como entero a propósito (varias están marcadas [suave] "
        "en el modelo de datos: 'se integra si está, funciona igual si no')\n"
        "y en los dos casos sacala de REFERENCIAS_PENDIENTES, en "
        "core/tests/test_referencias_pendientes.py, explicando qué se hizo."
    )


@pytest.mark.parametrize(
    "clave,valor", sorted(REFERENCIAS_PENDIENTES.items()), ids=str
)
def test_el_campo_declarado_existe_de_verdad(clave, valor):
    app, modelo, campo = clave

    try:
        cls = apps.get_model(app, modelo)
    except LookupError:
        pytest.fail(
            f"REFERENCIAS_PENDIENTES declara {app}.{modelo}, que ya no existe. "
            f"Sacá la entrada o corregí el nombre."
        )

    try:
        cls._meta.get_field(campo)
    except FieldDoesNotExist:
        pytest.fail(
            f"{app}.{modelo} no tiene el campo '{campo}'. Si lo renombraste, "
            f"actualizá la entrada en REFERENCIAS_PENDIENTES; si lo convertiste "
            f"en FK, sacala."
        )


@pytest.mark.parametrize(
    "clave,valor", sorted(REFERENCIAS_PENDIENTES.items()), ids=str
)
def test_cada_referencia_explica_por_que_quedo_pendiente(clave, valor):
    """
    El motivo lo va a leer otra persona, meses después, cuando el test se
    ponga rojo. Un "falta la tabla" no le alcanza para decidir.
    """
    _, motivo = valor

    assert len(motivo.strip()) >= 30, (
        f"La referencia {clave} no explica nada: '{motivo}'. Escribí de qué "
        f"módulo es la tabla destino, si el modelo de datos la marca [suave], y si "
        f"hay código leyendo ese entero hoy."
    )


def test_el_campo_declarado_no_es_ya_una_fk():
    convertidas = []

    for (app, modelo, campo), _ in REFERENCIAS_PENDIENTES.items():
        try:
            cls = apps.get_model(app, modelo)
            field = cls._meta.get_field(campo)
        except (LookupError, FieldDoesNotExist):
            continue  # lo cubre el test de arriba

        if field.is_relation:
            convertidas.append(f"{app}.{modelo}.{campo}")

    assert not convertidas, (
        f"Estos campos ya son una relación y siguen declarados como "
        f"pendientes: {sorted(convertidas)}. Sacalos de "
        f"REFERENCIAS_PENDIENTES."
    )
