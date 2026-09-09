import pytest


@pytest.fixture
def espanol(db):
    from comun.idiomas import api as idiomas

    return idiomas.crear_idioma(codigo="es", nombre="Español")


@pytest.fixture
def ingles(db):
    from comun.idiomas import api as idiomas

    return idiomas.crear_idioma(codigo="en", nombre="Inglés")
