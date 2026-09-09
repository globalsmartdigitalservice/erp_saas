"""
Acceso a datos de `EmpresaMoneda`.

Es TENANT, igual que `EmpresaPais`, y con el mismo detalle: **el alta la
hace el proveedor sin empresa en el contexto**, así que las funciones
que reciben `empresa_id` explícito van dentro de `sin_filtro_de_empresa()`.
Sin eso, el `save()` de ModeloTenant iría a buscar la empresa al
contexto —vacío— y la fila nacería sin dueño.
"""

from comun.empresas.models import EmpresaMoneda
from core.tenancy import sin_filtro_de_empresa


def obtener(empresa_moneda_id: int) -> EmpresaMoneda | None:
    return EmpresaMoneda.objects.filter(pk=empresa_moneda_id).first()


def listar_de(empresa_id: int) -> list[EmpresaMoneda]:
    """Las monedas con las que opera una empresa."""
    with sin_filtro_de_empresa():
        return list(EmpresaMoneda.objects.filter(empresa_id=empresa_id))


def obtener_oficial_de(empresa_id: int) -> EmpresaMoneda | None:
    """
    La fila marcada como oficial. Es la que reemplaza a la columna
    `Empresa.monedaOficialId` que el modelo de datos ya no tiene.
    """
    with sin_filtro_de_empresa():
        return EmpresaMoneda.objects.filter(
            empresa_id=empresa_id, es_moneda_oficial=True
        ).first()


def existe(empresa_id: int, moneda_id: int) -> bool:
    """Contra la constraint única (empresa, moneda)."""
    with sin_filtro_de_empresa():
        return EmpresaMoneda.objects.filter(
            empresa_id=empresa_id, moneda_id=moneda_id
        ).exists()


def hay_empresas_con_moneda(moneda_id: int) -> bool:
    """¿Alguna empresa del sistema opera con esa moneda?"""
    with sin_filtro_de_empresa():
        return EmpresaMoneda.objects.filter(moneda_id=moneda_id).exists()


def desmarcar_oficiales(empresa_id: int, excluir_id: int | None = None) -> int:
    """
    Deja en `false` la oficial de ESA empresa.

    Va acotada por empresa a propósito: antes esto era global —había una
    sola oficial en todo el sistema— y ése era justamente el error que
    el modelo de datos corrige. Corre dentro de la transacción del service que está
    marcando la nueva, así que nunca se ve un estado con dos ni con
    ninguna.
    """
    with sin_filtro_de_empresa():
        qs = EmpresaMoneda.objects.filter(
            empresa_id=empresa_id, es_moneda_oficial=True
        )
        if excluir_id is not None:
            qs = qs.exclude(pk=excluir_id)
        return qs.update(es_moneda_oficial=False)


def crear(
    *, empresa_id: int, moneda_id: int, es_moneda_oficial: bool, estado_id: int
) -> EmpresaMoneda:
    with sin_filtro_de_empresa():
        return EmpresaMoneda.objects.create(
            empresa_id=empresa_id,
            moneda_id=moneda_id,
            es_moneda_oficial=es_moneda_oficial,
            estado_id=estado_id,
        )


def actualizar(fila: EmpresaMoneda, **campos) -> EmpresaMoneda:
    with sin_filtro_de_empresa():
        for campo, valor in campos.items():
            setattr(fila, campo, valor)
        fila.save(update_fields=list(campos))
    return fila
