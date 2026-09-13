"""Superficie pública de `empresas`. El resto de la app es privado.

Nada de acá filtra por empresa activa: `Empresa` no es un `ModeloTenant`
—un `empresa_id` apuntaría a sí misma—, así que estas funciones ven todas
las empresas del sistema. Quién puede llamarlas lo decide la capa de
arriba.
"""


from comun.empresas.models import Empresa, EmpresaMoneda, EmpresaPais
from comun.empresas.repository import empresa as _repo
from comun.empresas.repository import empresa_moneda as _repo_moneda
from comun.empresas.repository import empresa_pais as _repo_pais
from comun.empresas.services import empresa as _svc
from comun.empresas.services import empresa_moneda as _svc_moneda
from comun.empresas.services import empresa_pais as _svc_pais


def obtener_empresa(empresa_id: int) -> Empresa | None:
    return _repo.obtener(empresa_id)


def obtener_empresas(empresa_ids) -> dict[int, Empresa]:
    return _repo.obtener_varias(empresa_ids)


def listar_empresas() -> list[Empresa]:
    return _repo.listar()


def listar_matrices() -> list[Empresa]:
    """Las que no dependen de ninguna otra. Un cliente = una matriz."""
    return _repo.listar_matrices()


def sucursales_de(empresa_id: int) -> list[Empresa]:
    """Las hijas DIRECTAS."""
    return _repo.listar_sucursales_de(empresa_id)


def descendientes_de(empresa_id: int) -> list[Empresa]:
    """La empresa y todas sus sucursales. Devuelve la lista: cada operación
    se hace después parada en cada empresa, no comparte datos."""
    return _svc.descendientes_de(empresa_id)


def matriz_de(empresa_id: int) -> Empresa | None:
    """La casa matriz del grupo. Si ya es matriz, se devuelve ella."""
    return _svc.matriz_de(empresa_id)


def exigir_del_grupo(empresa_id: int) -> int:
    """El id, solo si es del grupo del cliente de la sesión. Si no lo es,
    falla como si la empresa no existiera."""
    return _svc.exigir_del_grupo(empresa_id)


def ids_del_ambito(empresa_id: int) -> list[int]:
    """Los ids cuya CONFIGURACIÓN ve esta empresa: ella y su matriz. **No se
    usa para datos**: las ventas y el stock siguen con filtro exacto."""
    return _svc.ids_del_ambito(empresa_id)


def hay_empresas_con_idioma(idioma_id: int) -> bool:
    """Para el invariante de `idiomas`: no desactivar un idioma en uso."""
    return _repo.hay_con_idioma(idioma_id)


def idioma_de(empresa_id: int) -> int | None:
    """Devuelve el ID y no el objeto: quien lo llama solo necesita el
    número, y traer el objeto sería una consulta más."""
    empresa = _repo.obtener(empresa_id)
    return empresa.idioma_default_id if empresa else None


def hay_empresas_con_moneda(moneda_id: int) -> bool:
    """¿Alguna empresa del sistema opera con esa moneda?"""
    return _repo_moneda.hay_empresas_con_moneda(moneda_id)


def moneda_oficial_de(empresa_id: int):
    """La moneda base de UNA empresa.  No hay una "moneda oficial del
   sistema": el boliviano lleva BOB y el peruano PEN, en la misma
   instalación."""
    return _svc_moneda.moneda_oficial_de(empresa_id)


def listar_monedas_de(empresa_id: int) -> list[EmpresaMoneda]:
    """Todas las monedas con las que opera una empresa, no solo la base."""
    return _svc_moneda.listar_de(empresa_id)


def listar_paises_de(empresa_id: int) -> list[EmpresaPais]:
    """Reemplaza al accesor inverso `empresa.paises`, que no existe porque
    `ModeloTenant` declara la FK con `related_name="+"`."""
    return _repo_pais.listar_de(empresa_id)


def crear_empresa(**datos) -> Empresa:
    return _svc.crear(**datos)


def actualizar_empresa(empresa_id: int, **campos) -> Empresa:
    return _svc.actualizar(empresa_id, **campos)


def desactivar_empresa(empresa_id: int) -> Empresa:
    """Soft delete. Falla si tiene sucursales activas."""
    return _svc.desactivar(empresa_id)


def agregar_pais(**datos) -> EmpresaPais:
    return _svc_pais.agregar(**datos)


def agregar_moneda(
    *, empresa_id: int, moneda_id: int, es_moneda_oficial: bool = False
) -> EmpresaMoneda:
    """La primera moneda es siempre la oficial: sin base de conversión no hay
    `montoBase`."""
    return _svc_moneda.agregar(
        empresa_id=empresa_id,
        moneda_id=moneda_id,
        es_moneda_oficial=es_moneda_oficial,
    )


def marcar_moneda_oficial(empresa_id: int, moneda_id: int) -> EmpresaMoneda:
    """Cambia la moneda base de una empresa. Desmarca la anterior."""
    return _svc_moneda.marcar_oficial(empresa_id, moneda_id)


def quitar_moneda(empresa_id: int, moneda_id: int) -> int:
    """Soft delete. Falla si es la oficial: la empresa quedaría sin base."""
    return _svc_moneda.quitar(empresa_id, moneda_id)


def actualizar_pais(empresa_pais_id: int, **campos) -> EmpresaPais:
    return _svc_pais.actualizar(empresa_pais_id, **campos)


__all__ = [
    "obtener_empresa",
    "obtener_empresas",
    "listar_empresas",
    "listar_matrices",
    "sucursales_de",
    "matriz_de",
    "descendientes_de",
    "ids_del_ambito",
    "exigir_del_grupo",
    "hay_empresas_con_idioma",
    "idioma_de",
    "hay_empresas_con_moneda",
    "moneda_oficial_de",
    "listar_monedas_de",
    "listar_paises_de",
    "crear_empresa",
    "actualizar_empresa",
    "desactivar_empresa",
    "agregar_pais",
    "agregar_moneda",
    "marcar_moneda_oficial",
    "quitar_moneda",
    "actualizar_pais",
]
