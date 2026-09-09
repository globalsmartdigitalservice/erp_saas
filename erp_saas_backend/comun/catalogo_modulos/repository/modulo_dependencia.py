"""Acceso a datos de `Modulo_Dependencia`. Catálogo del proveedor, sin filtro."""

from comun.catalogo_modulos.models import ModuloDependencia


def obtener(modulo_id: int, depende_de_id: int) -> ModuloDependencia | None:
    return ModuloDependencia.objects.filter(
        modulo_id=modulo_id, depende_de_id=depende_de_id
    ).first()


def existe(modulo_id: int, depende_de_id: int) -> bool:
    return ModuloDependencia.objects.filter(
        modulo_id=modulo_id, depende_de_id=depende_de_id
    ).exists()


def listar_de(modulo_id: int) -> list[ModuloDependencia]:
    """Las dependencias DIRECTAS. Para la cadena completa está el service."""
    return list(ModuloDependencia.objects.filter(modulo_id=modulo_id))


def ids_requeridos_por(modulo_id: int) -> list[int]:
    return list(
        ModuloDependencia.objects.filter(modulo_id=modulo_id).values_list(
            "depende_de_id", flat=True
        )
    )


def listar_que_dependen_de(modulo_id: int) -> list[ModuloDependencia]:
    """Al revés: quién quedaría roto si este módulo se da de baja."""
    return list(ModuloDependencia.objects.filter(depende_de_id=modulo_id))


def crear(**campos) -> ModuloDependencia:
    return ModuloDependencia.objects.create(**campos)


def eliminar(fila: ModuloDependencia) -> None:
    fila.delete()
