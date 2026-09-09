import pytest
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.test.utils import isolate_apps

from core.tenancy import (
    ModeloTenant,
    ModeloTenantDerivado,
    SinEmpresaEnContexto,
    empresa,
    sin_filtro_de_empresa,
)


def _sql(qs) -> str:
    return str(qs.query).lower()


@isolate_apps("comun.tipologias")
def test_la_consulta_salta_al_padre_para_filtrar():

    class Empresa(models.Model):
        class Meta:
            app_label = "tipologias"

    class Pedido(models.Model):
        empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name="+")

        class Meta:
            app_label = "tipologias"

    class DetallePedido(ModeloTenantDerivado):
        RUTA_A_EMPRESA = "pedido"

        pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="+")

        class Meta:
            app_label = "tipologias"

    with empresa(7):
        sql = _sql(DetallePedido.objects.all())

    assert "join" in sql, (
        "La consulta no salta al padre. Sin ese JOIN, DetallePedido.objects.all() "
        "devuelve las filas de TODOS los clientes."
    )
    assert "empresa_id" in sql and "7" in sql, (
        f"La consulta no filtra por la empresa del contexto. SQL: {sql}"
    )


@isolate_apps("comun.tipologias")
def test_la_ruta_puede_tener_varios_saltos():

    class Empresa(models.Model):
        class Meta:
            app_label = "tipologias"

    class Pedido(models.Model):
        empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name="+")

        class Meta:
            app_label = "tipologias"

    class Documento(models.Model):
        pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="+")

        class Meta:
            app_label = "tipologias"

    class DetalleDocumento(ModeloTenantDerivado):
        RUTA_A_EMPRESA = "documento__pedido"

        documento = models.ForeignKey(
            Documento, on_delete=models.CASCADE, related_name="+"
        )

        class Meta:
            app_label = "tipologias"

    with empresa(7):
        sql = _sql(DetalleDocumento.objects.all())

    assert sql.count("join") >= 2, (
        f"La ruta de dos saltos no generó los dos JOIN. SQL: {sql}"
    )
    assert "empresa_id" in sql


@isolate_apps("comun.tipologias")
def test_sin_empresa_en_el_contexto_revienta():

    class Empresa(models.Model):
        class Meta:
            app_label = "tipologias"

    class Pedido(models.Model):
        empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name="+")

        class Meta:
            app_label = "tipologias"

    class DetallePedido(ModeloTenantDerivado):
        RUTA_A_EMPRESA = "pedido"

        pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="+")

        class Meta:
            app_label = "tipologias"

    with pytest.raises(SinEmpresaEnContexto):
        DetallePedido.objects.all()


@isolate_apps("comun.tipologias")
def test_la_puerta_de_salida_desactiva_el_filtro():

    class Empresa(models.Model):
        class Meta:
            app_label = "tipologias"

    class Pedido(models.Model):
        empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name="+")

        class Meta:
            app_label = "tipologias"

    class DetallePedido(ModeloTenantDerivado):
        RUTA_A_EMPRESA = "pedido"

        pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="+")

        class Meta:
            app_label = "tipologias"

    with empresa(7):
        with sin_filtro_de_empresa():
            sql = _sql(DetallePedido.objects.all())

    assert "join" not in sql, (
        f"Con el filtro desactivado no debería haber JOIN al padre. SQL: {sql}"
    )


@isolate_apps("comun.tipologias")
def test_heredar_sin_declarar_la_ruta_revienta():

    class SinRuta(ModeloTenantDerivado):
        class Meta:
            app_label = "tipologias"

    with empresa(7):
        with pytest.raises(ImproperlyConfigured, match="RUTA_A_EMPRESA"):
            SinRuta.objects.all()


def test_toda_subclase_declara_una_ruta_que_resuelve():
    from django.apps import apps
    from django.core.exceptions import FieldError

    PREFIJOS = ("core.", "comun.", "servicios.", "dominios.", "procesos.",
                "complementos.", "proveedor.")

    problemas = []

    for modelo in apps.get_models():
        if not modelo._meta.app_config.name.startswith(PREFIJOS):
            continue
        if not issubclass(modelo, ModeloTenantDerivado):
            continue

        ruta = getattr(modelo, "RUTA_A_EMPRESA", "")
        if not ruta:
            problemas.append(f"{modelo.__name__}: no declaró RUTA_A_EMPRESA")
            continue

        try:
            with sin_filtro_de_empresa():
                str(modelo.objects.filter(**{f"{ruta}__empresa_id": 1}).query)
        except (FieldError, ValueError) as error:
            problemas.append(f"{modelo.__name__}: RUTA_A_EMPRESA='{ruta}' → {error}")

    assert not problemas, (
        "Estas tablas heredan ModeloTenantDerivado y su ruta al padre no "
        "sirve: " + "; ".join(problemas) + ". Una ruta que no resuelve deja "
        "la tabla sin aislar hasta la primera consulta real."
    )


def test_las_dos_clases_base_no_se_mezclan():
    from django.apps import apps

    mezcladas = [
        m.__name__
        for m in apps.get_models()
        if issubclass(m, ModeloTenantDerivado) and issubclass(m, ModeloTenant)
    ]

    assert not mezcladas, (
        f"Estos modelos heredan de ModeloTenant y de ModeloTenantDerivado a la "
        f"vez: {sorted(mezcladas)}. Elegí uno: o lleva su empresa_id, o la "
        f"deriva del padre."
    )
