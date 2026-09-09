from pathlib import Path

import pytest
from django.apps import apps

from comun.idiomas import traducibles



PENDIENTES: dict[str, str] = {}

LLAMADA = "traducciones_de"


def _fuentes_graphql(modelo) -> list[Path]:
    """Los .py del `graphql/` de la app dueña de esa tabla."""
    carpeta = Path(apps.get_app_config(modelo._meta.app_label).path) / "graphql"
    if not carpeta.is_dir():
        return []
    return sorted(carpeta.glob("*.py"))


def _modelo_de(tabla: str):
    for modelo in apps.get_models():
        if modelo._meta.db_table == tabla:
            return modelo
    return None


def _traduce(tabla: str) -> bool:
    modelo = _modelo_de(tabla)
    if modelo is None:
        return False

    return any(
        LLAMADA in fuente.read_text(encoding="utf-8")
        for fuente in _fuentes_graphql(modelo)
    )


@pytest.mark.parametrize("tabla", sorted(traducibles.TRADUCIBLES))
def test_toda_tabla_traducible_tiene_quien_la_traduzca(tabla):
    if tabla in PENDIENTES:
        pytest.skip(f"Pendiente declarado: {PENDIENTES[tabla]}")

    assert _traduce(tabla), (
        f"'{tabla}' está declarada como traducible pero el `graphql/` de su "
        f"app nunca llama a `{LLAMADA}`, así que sus textos van a salir "
        f"siempre en el idioma en que fueron cargados y nadie se va a "
        f"enterar.\n\n"
        f"Copiá `_traducidas()` de comun/tipologias/graphql/queries.py. Si no "
        f"se puede hacer ahora, declarala en PENDIENTES con el motivo, en "
        f"core/tests/test_traducciones_enchufadas.py."
    )


def test_la_lista_de_pendientes_no_se_pudre():
    declaradas = set(PENDIENTES)
    traducibles_hoy = set(traducibles.TRADUCIBLES)

    fantasmas = declaradas - traducibles_hoy
    assert not fantasmas, (
        f"Estas tablas están en PENDIENTES pero ya no son traducibles: "
        f"{sorted(fantasmas)}. Saquenlas de la lista."
    )

    ya_hechas = {tabla for tabla in declaradas if _traduce(tabla)}
    assert not ya_hechas, (
        f"Estas ya traducen y siguen declaradas como pendientes: "
        f"{sorted(ya_hechas)}. Saquenlas para que el test las vigile de verdad."
    )

    sin_motivo = {
        tabla for tabla, motivo in PENDIENTES.items() if len(motivo.strip()) < 30
    }
    assert not sin_motivo, (
        f"Estas no explican por qué están pendientes: {sorted(sin_motivo)}. "
        f'"Falta hacerlo" no es un motivo: escribí cuándo y por qué no ahora.'
    )
