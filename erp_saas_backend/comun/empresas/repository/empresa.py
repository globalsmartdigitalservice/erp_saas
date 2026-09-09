"""
Acceso a datos de `Empresa`.

OJO: `Empresa` NO es un `ModeloTenant` —es la tabla *de* empresas—, así
que su manager es el normal de Django y NO filtra por empresa activa.
Todo lo de acá ve todas las empresas del sistema; quién puede llamarlo
lo decide la capa de arriba.
"""

from comun.empresas.models import Empresa


def obtener(empresa_id: int) -> Empresa | None:
    return Empresa.objects.filter(pk=empresa_id).first()


def obtener_varias(empresa_ids) -> dict[int, Empresa]:
    return {e.pk: e for e in Empresa.objects.filter(pk__in=list(empresa_ids))}


def listar() -> list[Empresa]:
    return list(Empresa.objects.all())


def listar_matrices() -> list[Empresa]:
    return list(Empresa.objects.filter(empresa_padre__isnull=True))


def listar_sucursales_de(empresa_id: int) -> list[Empresa]:
    """Las hijas DIRECTAS. Para todo el grupo hace falta recorrer."""
    return list(Empresa.objects.filter(empresa_padre_id=empresa_id))


def listar_sucursales_de_varias(empresa_ids) -> list[Empresa]:
    """Las hijas directas de VARIAS empresas en UNA consulta: sin esto, un
    grupo de 20 sucursales dispara 21."""
    return list(Empresa.objects.filter(empresa_padre_id__in=list(empresa_ids)))


def existe_matriz_con_identificacion(
    ident_tributaria: str, pais_id: int, excluir_id: int | None = None
) -> bool:
    """¿Hay otra CASA MATRIZ del MISMO PAÍS con esa identificación?

    Cruza `empresa_pais` porque el país no es columna de `empresa`, y por eso
    la regla no puede ser una constraint. Va dentro de `sin_filtro_de_empresa()`
    porque `EmpresaPais` es tenant y acá se busca ENTRE empresas."""
    from core.tenancy import sin_filtro_de_empresa

    from comun.empresas.models import EmpresaPais

    with sin_filtro_de_empresa():
        del_pais = EmpresaPais.objects.filter(pais_id=pais_id).values("empresa_id")

        qs = Empresa.objects.filter(
            ident_tributaria=ident_tributaria,
            empresa_padre__isnull=True,
            pk__in=del_pais,
        )
        if excluir_id is not None:
            qs = qs.exclude(pk=excluir_id)
        return qs.exists()


def hay_con_idioma(idioma_id: int) -> bool:
    """Para el invariante de `idiomas`: no desactivar un idioma en uso."""
    return Empresa.objects.filter(idioma_default_id=idioma_id).exists()


def hay_con_moneda(moneda_id: int) -> bool:
    """Ya no se responde acá: la moneda de una empresa vive en
    `empresa_moneda`. Lo contesta su repository."""
    from comun.empresas.repository import empresa_moneda as repo_moneda

    return repo_moneda.hay_empresas_con_moneda(moneda_id)


def crear(**campos) -> Empresa:
    return Empresa.objects.create(**campos)


def actualizar(empresa: Empresa, **campos) -> Empresa:
    for campo, valor in campos.items():
        setattr(empresa, campo, valor)
    empresa.save(update_fields=list(campos))
    return empresa
