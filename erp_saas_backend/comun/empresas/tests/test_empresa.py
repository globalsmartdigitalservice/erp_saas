import pytest
from django.core.exceptions import ValidationError

from comun.empresas import api as empresas

pytestmark = pytest.mark.django_db


def test_crear_empresa_crea_tambien_su_pais(datos_base, catalogo_empresas):
    empresa = empresas.crear_empresa(
        ident_tributaria="1234567", razon_social="Ferretería S.A.", **datos_base
    )

    assert empresa.pk is not None
    assert empresa.es_matriz is True

    paises = empresas.listar_paises_de(empresa.pk)
    assert len(paises) == 1
    assert paises[0].pais_id == catalogo_empresas["bolivia"].pk


def test_el_rubro_no_puede_ser_un_estado(datos_base, catalogo_empresas):
    """Las tres FK apuntan a `tipologia` entera: Postgres acepta cualquier
    fila y el catálogo se mezcla en silencio."""
    datos = {**datos_base, "rubro_id": catalogo_empresas["activa"].pk}

    with pytest.raises(ValidationError, match="Se esperaba un valor de 'rubro'"):
        empresas.crear_empresa(
            ident_tributaria="1", razon_social="X", **datos
        )


def test_el_tipo_no_puede_ser_un_rubro(datos_base, catalogo_empresas):
    datos = {**datos_base, "tipo_empresa_id": catalogo_empresas["rubro"].pk}

    with pytest.raises(ValidationError, match="Se esperaba un valor de 'tipo_empresa'"):
        empresas.crear_empresa(ident_tributaria="1", razon_social="X", **datos)


def test_una_casa_matriz_no_puede_tener_padre(matriz, datos_base):
    with pytest.raises(ValidationError, match="no puede depender de otra"):
        empresas.crear_empresa(
            ident_tributaria="999",
            razon_social="Otra",
            empresa_padre_id=matriz.pk,
            **datos_base,
        )


def test_una_sucursal_sin_padre_se_rechaza(datos_base, catalogo_empresas):
    datos = {**datos_base, "tipo_empresa_id": catalogo_empresas["tipo_sucursal"].pk}

    with pytest.raises(ValidationError, match="tiene que tener una empresa padre"):
        empresas.crear_empresa(ident_tributaria="1", razon_social="X", **datos)


def test_la_sucursal_comparte_el_nit_de_su_matriz(sucursal, matriz):
    assert sucursal.ident_tributaria == matriz.ident_tributaria
    assert sucursal.empresa_padre_id == matriz.pk


def test_dos_matrices_del_mismo_pais_no_comparten_nit(matriz, datos_base):
    with pytest.raises(ValidationError, match="mismo contribuyente"):
        empresas.crear_empresa(
            ident_tributaria="1234567", razon_social="Otra distinta", **datos_base
        )


def test_dos_matrices_de_PAISES_DISTINTOS_si_pueden_compartir_nit(
    matriz, datos_base, catalogo_empresas
):
    datos = {**datos_base, "pais_id": catalogo_empresas["peru"].pk}

    peruana = empresas.crear_empresa(
        ident_tributaria="1234567", razon_social="Ferretería Peruana S.A.C.", **datos
    )

    assert peruana.pk != matriz.pk


def test_una_empresa_no_puede_ser_su_propia_matriz(matriz, catalogo_empresas):
    with pytest.raises(ValidationError, match="su propia matriz"):
        empresas.actualizar_empresa(
            matriz.pk,
            empresa_padre_id=matriz.pk,
            tipo_empresa_id=catalogo_empresas["tipo_sucursal"].pk,
        )


def test_no_se_puede_cerrar_un_ciclo(matriz, sucursal, catalogo_empresas):
    with pytest.raises(ValidationError, match="ciclo"):
        empresas.actualizar_empresa(
            matriz.pk,
            empresa_padre_id=sucursal.pk,
            tipo_empresa_id=catalogo_empresas["tipo_sucursal"].pk,
        )


def test_no_se_desactiva_una_matriz_con_sucursales_activas(matriz, sucursal):
    with pytest.raises(ValidationError, match="sucursal"):
        empresas.desactivar_empresa(matriz.pk)


def test_si_las_sucursales_ya_estan_de_baja_la_matriz_si_se_desactiva(
    matriz, sucursal, catalogo_empresas
):
    empresas.desactivar_empresa(sucursal.pk)
    empresas.desactivar_empresa(matriz.pk)

    assert (
        empresas.obtener_empresa(matriz.pk).estado_id
        == catalogo_empresas["inactiva"].pk
    )


def test_desactivar_es_soft_delete(matriz, catalogo_empresas):
    empresas.desactivar_empresa(matriz.pk)

    assert empresas.obtener_empresa(matriz.pk) is not None


def test_matriz_de_una_sucursal(sucursal, matriz):
    assert empresas.matriz_de(sucursal.pk).pk == matriz.pk


def test_matriz_de_una_matriz_es_ella_misma(matriz):
    assert empresas.matriz_de(matriz.pk).pk == matriz.pk


def test_el_ambito_de_una_sucursal_incluye_a_su_matriz(sucursal, matriz):
    assert set(empresas.ids_del_ambito(sucursal.pk)) == {sucursal.pk, matriz.pk}


def test_el_ambito_de_una_matriz_es_solo_ella(matriz):
    assert empresas.ids_del_ambito(matriz.pk) == [matriz.pk]


#
# Lo consume `membresias.afiliar_al_grupo` y lo va a
# consumir el consolidado del grupo cuando exista.


def test_los_descendientes_de_una_matriz_la_incluyen_a_ella(matriz, sucursal):
    ids = {e.pk for e in empresas.descendientes_de(matriz.pk)}

    assert ids == {matriz.pk, sucursal.pk}


def test_los_descendientes_de_una_sucursal_son_solo_ella(matriz, sucursal):
    ids = [e.pk for e in empresas.descendientes_de(sucursal.pk)]

    assert ids == [sucursal.pk]


def test_baja_por_todos_los_niveles(matriz, sucursal, crear_sucursal_de):
    nieta = crear_sucursal_de(sucursal, "Depósito de la Sucursal")

    ids = {e.pk for e in empresas.descendientes_de(matriz.pk)}

    assert ids == {matriz.pk, sucursal.pk, nieta.pk}


def test_no_se_cuelga_con_un_ciclo(matriz, sucursal):
    from comun.empresas.models import Empresa

    Empresa.objects.filter(pk=matriz.pk).update(empresa_padre_id=sucursal.pk)

    ids = {e.pk for e in empresas.descendientes_de(matriz.pk)}

    assert ids == {matriz.pk, sucursal.pk}


def test_de_una_empresa_que_no_existe_no_devuelve_nada(db):
    assert empresas.descendientes_de(999999) == []


def test_no_se_lleva_a_la_empresa_de_otro_cliente(matriz, sucursal, otra_empresa):
    ids = {e.pk for e in empresas.descendientes_de(matriz.pk)}

    assert otra_empresa.pk not in ids


def test_hay_empresas_con_idioma(matriz, catalogo_empresas):
    assert empresas.hay_empresas_con_idioma(catalogo_empresas["idioma"].pk) is True


def test_no_se_puede_desactivar_el_idioma_de_una_empresa(matriz, catalogo_empresas):
    from comun.idiomas import api as idiomas

    with pytest.raises(ValidationError, match="no se puede desactivar"):
        idiomas.desactivar_idioma(catalogo_empresas["idioma"].pk)
