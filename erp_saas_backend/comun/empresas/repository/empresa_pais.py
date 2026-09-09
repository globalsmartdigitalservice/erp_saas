"""
Acceso a datos de `EmpresaPais`.

Es TENANT: su manager filtra solo por la empresa del contexto. Las
funciones que tienen que cruzar empresas —el onboarding, que corre sin
contexto— usan `sin_filtro_de_empresa()` explícito y dicen por qué.
"""

from comun.empresas.models import EmpresaPais
from core.tenancy import sin_filtro_de_empresa


def obtener(empresa_pais_id: int) -> EmpresaPais | None:
    return EmpresaPais.objects.filter(pk=empresa_pais_id).first()


def listar_de(empresa_id: int) -> list[EmpresaPais]:
    """
    Los países de UNA empresa.

    Reemplaza al accesor inverso `empresa.paises`, que ModeloTenant no
    deja existir (`related_name="+"`).

    Va con la puerta de salida porque quien consulta puede ser el panel
    del proveedor, sin empresa en el contexto; el filtro por empresa lo
    pone el parámetro, explícito.
    """
    with sin_filtro_de_empresa():
        return list(EmpresaPais.objects.filter(empresa_id=empresa_id))


def existe(empresa_id: int, pais_id: int) -> bool:
    """Contra la constraint única (empresa, pais)."""
    with sin_filtro_de_empresa():
        return EmpresaPais.objects.filter(
            empresa_id=empresa_id, pais_id=pais_id
        ).exists()


def crear(*, empresa_id: int, pais_id: int, **campos) -> EmpresaPais:
    """
    El alta la hace el PROVEEDOR, sin empresa en el contexto: por eso la
    empresa se pasa explícita y va dentro de la puerta de salida. Sin
    eso, el `save()` de ModeloTenant intentaría tomarla del contexto y
    la dejaría en None.
    """
    with sin_filtro_de_empresa():
        return EmpresaPais.objects.create(
            empresa_id=empresa_id, pais_id=pais_id, **campos
        )


def actualizar(empresa_pais: EmpresaPais, **campos) -> EmpresaPais:
    with sin_filtro_de_empresa():
        for campo, valor in campos.items():
            setattr(empresa_pais, campo, valor)
        empresa_pais.save(update_fields=list(campos))
    return empresa_pais
