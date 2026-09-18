import ast
import datetime
import inspect

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError

from comun.membresias import api as membresias
from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_BAJA
from core.tenancy import empresa
from core.tests.afiliacion import afiliar_en
from core.tests.permisos import darle_el_permiso
from dominios.seguridad import api as seguridad
from dominios.seguridad.permisos import content_type_del_ancla
from dominios.seguridad.services import grupo_empresa, grupo_usuario

Usuario = get_user_model()


MODULOS = (grupo_usuario, grupo_empresa)

COMPUERTA = "preserva_quien_administra"


SIN_COMPUERTA = {
    "grupo_usuario.asignar": (
        "Solo agrega una asignación. La compuerta es 'no empeorar', así que "
        "sobre un alta no puede disparar nunca."
    ),
    "grupo_empresa.crear": (
        "Solo agrega un rol, y un rol recién creado no se lo quita a nadie."
    ),
    "grupo_empresa.agregar_permiso": (
        "Solo agrega un permiso a un rol: otorga más, nunca menos. Lo que "
        "limita cuánto se puede otorgar es la atenuación, no esta compuerta."
    ),
}


def _escrituras():
    for modulo in MODULOS:
        nombre_modulo = modulo.__name__.rsplit(".", 1)[-1]
        arbol = ast.parse(inspect.getsource(modulo))
        for nodo in arbol.body:
            if isinstance(nodo, ast.FunctionDef) and _es_atomica(nodo):
                yield f"{nombre_modulo}.{nodo.name}", _lleva_compuerta(nodo)


def _decoradores(nodo):
    return {ast.unparse(d) for d in nodo.decorator_list}


def _es_atomica(nodo):
    return "transaction.atomic" in _decoradores(nodo)


def _lleva_compuerta(nodo):
    return COMPUERTA in _decoradores(nodo)


def test_toda_escritura_lleva_la_compuerta_o_esta_declarada():
    sin_declarar = [
        nombre
        for nombre, tiene in _escrituras()
        if not tiene and nombre not in SIN_COMPUERTA
    ]

    assert not sin_declarar, (
        "Estas operaciones escriben en el grafo de seguridad y no llevan "
        f"@{COMPUERTA}: " + ", ".join(sorted(sin_declarar)) + ". Si puede "
        "dejar la cadena otorgando menos —quitar, dar de baja, poner fecha de "
        "fin o cambiar un estado—, ponele el decorador: sin él, la empresa "
        "puede quedarse sin nadie que asigne roles y no hay forma de "
        "repoblarla. Si solo agrega, declarala en SIN_COMPUERTA con el "
        "motivo, en dominios/seguridad/tests/test_compuerta.py."
    )


def test_no_hay_declaraciones_de_operaciones_que_ya_no_existen():
    existentes = {nombre for nombre, _ in _escrituras()}
    fantasmas = [n for n in SIN_COMPUERTA if n not in existentes]

    assert not fantasmas, (
        f"Estas operaciones están declaradas en SIN_COMPUERTA y ya no existen: "
        f"{sorted(fantasmas)}. Sacalas de la lista."
    )


def test_ninguna_declaracion_lleva_ya_la_compuerta():
    contradicciones = [
        nombre for nombre, tiene in _escrituras() if tiene and nombre in SIN_COMPUERTA
    ]

    assert not contradicciones, (
        f"Estas operaciones llevan la compuerta y además figuran en "
        f"SIN_COMPUERTA: {sorted(contradicciones)}. Sacalas de la lista."
    )


@pytest.mark.parametrize("nombre,motivo", sorted(SIN_COMPUERTA.items()))
def test_cada_declaracion_tiene_un_motivo_de_verdad(nombre, motivo):
    assert len(motivo.strip()) > 30, (
        f"{nombre} está declarada sin explicar por qué no lleva la compuerta."
    )


def test_el_detector_agarra_una_escritura_sin_compuerta():
    arbol = ast.parse(
        "@transaction.atomic\n"
        "def quitar_algo(x):\n"
        "    return x\n"
    )
    nodo = arbol.body[0]

    assert _es_atomica(nodo)
    assert not _lleva_compuerta(nodo)


LLAVE = "segu_roles_asignar_rol"


@pytest.fixture
def activo(catalogo):
    return catalogo["estado_activo"]


@pytest.fixture
def de_baja(catalogo):
    return catalogo["tipologia"](AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_BAJA)


@pytest.fixture
def permiso_llave(db):
    return Permission.objects.get_or_create(
        content_type=content_type_del_ancla(),
        codename=LLAVE,
        defaults={"name": LLAVE},
    )[0]


def _con_la_llave(nombre, la_empresa, activo, nombre_rol):
    cuenta = Usuario.objects.create_user(
        username=nombre,
        email=f"{nombre}@acme.com",
        password="Kx7pLm9Qw2",
        matriz=la_empresa,
    )
    afiliar_en(la_empresa.id, usuario_id=cuenta.id, estado_id=activo.id)
    darle_el_permiso(cuenta, la_empresa.id, activo.id, LLAVE, nombre_rol=nombre_rol)
    with empresa(la_empresa.id):
        membresia = membresias.membresia_de(cuenta.id)
        return seguridad.roles_vigentes_de_varias_membresias([membresia.id])[0]


@pytest.fixture
def llave(empresa_a, activo):
    return _con_la_llave("diego", empresa_a, activo, "Supervisor")


@pytest.mark.django_db
def test_no_se_le_quita_la_llave_al_rol_del_unico_administrador(
    empresa_a, llave, permiso_llave
):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError):
            seguridad.quitar_permiso(
                grupo_id=llave.grupo_empresa_id, auth_permission_id=permiso_llave.id
            )

        assert LLAVE in " ".join(seguridad.permisos_de(llave.usuario_empresa_id))


@pytest.mark.django_db
def test_no_se_da_de_baja_la_asignacion_del_unico_administrador(
    empresa_a, llave, de_baja
):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError):
            seguridad.actualizar_asignacion(llave.pk, estado_id=de_baja.id)

        assert seguridad.obtener_asignacion(llave.pk).estado_id != de_baja.id


@pytest.mark.django_db
def test_no_se_le_pone_fecha_de_fin_al_unico_administrador(empresa_a, llave):
    manana = datetime.date.today() + datetime.timedelta(days=1)

    with empresa(empresa_a.id):
        with pytest.raises(ValidationError):
            seguridad.actualizar_asignacion(llave.pk, fecha_fin=manana)

        assert seguridad.obtener_asignacion(llave.pk).fecha_fin is None


@pytest.mark.django_db
def test_no_se_da_de_baja_el_rol_del_unico_administrador(empresa_a, llave, de_baja):
    with empresa(empresa_a.id):
        with pytest.raises(ValidationError):
            seguridad.actualizar_rol(llave.grupo_empresa_id, estado_id=de_baja.id)

        assert LLAVE in " ".join(seguridad.permisos_de(llave.usuario_empresa_id))


@pytest.mark.django_db
def test_con_otro_administrador_permanente_la_llave_se_puede_quitar(
    empresa_a, llave, activo, permiso_llave
):
    _con_la_llave("carla", empresa_a, activo, "Gerencia")

    with empresa(empresa_a.id):
        seguridad.quitar_permiso(
            grupo_id=llave.grupo_empresa_id, auth_permission_id=permiso_llave.id
        )

        assert LLAVE not in " ".join(seguridad.permisos_de(llave.usuario_empresa_id))


@pytest.mark.django_db
def test_si_el_otro_administrador_vence_la_llave_no_se_puede_quitar(
    empresa_a, llave, activo, permiso_llave
):
    otra = _con_la_llave("carla", empresa_a, activo, "Gerencia")
    fin = datetime.date.today() + datetime.timedelta(days=90)

    with empresa(empresa_a.id):
        seguridad.actualizar_asignacion(otra.pk, fecha_fin=fin)

        with pytest.raises(ValidationError):
            seguridad.quitar_permiso(
                grupo_id=llave.grupo_empresa_id, auth_permission_id=permiso_llave.id
            )
