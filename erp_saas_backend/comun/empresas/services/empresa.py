from django.core.exceptions import ValidationError
from django.db import transaction

from comun.empresas.models import Empresa
from comun.empresas.repository import empresa as repo
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR
from core.tenancy import empresa_actual

# Un CONTRATO con la semilla, no etiquetas: el código busca estas filas
# POR NOMBRE. Si `cargar_tipologias.py` las escribe distinto, el alta de
# sucursal y la baja de empresa dejan de encontrar su fila.
NOMBRE_TIPO_MATRIZ = "CASA MATRIZ"
NOMBRE_ESTADO_ACTIVA = "ACTIVA"
NOMBRE_ESTADO_INACTIVA = "INACTIVA"


def _validar_tipologias(tipo_empresa_id: int, rubro_id: int, estado_id: int) -> None:
    for campo, valor, agrupador in (
        ("tipo_empresa", tipo_empresa_id, AGRUPADOR.TIPO_EMPRESA),
        ("rubro", rubro_id, AGRUPADOR.RUBRO),
        ("estado", estado_id, AGRUPADOR.ESTADO_EMPRESA),
    ):
        if valor is None:
            continue
        tipologias.exigir_del_agrupador(valor, agrupador, f"valor de '{campo}'")


def _es_tipo_matriz(tipo_empresa_id: int) -> bool:
    matriz = tipologias.obtener_del_sistema(
        AGRUPADOR.TIPO_EMPRESA, NOMBRE_TIPO_MATRIZ
    )
    if matriz is None:
        raise ValidationError(
            f"Falta la tipología '{NOMBRE_TIPO_MATRIZ}' del agrupador "
            f"TIPO_EMPRESA. Ejecute: python manage.py cargar_semillas"
        )
    return tipo_empresa_id == matriz.pk


def _validar_coherencia_jerarquia(
    tipo_empresa_id: int, empresa_padre_id: int | None
) -> None:
    es_matriz = _es_tipo_matriz(tipo_empresa_id)

    if es_matriz and empresa_padre_id is not None:
        raise ValidationError(
            "Una casa matriz no puede depender de otra empresa. O se le saca "
            "la empresa padre, o se la marca como sucursal o filial."
        )
    if not es_matriz and empresa_padre_id is None:
        raise ValidationError(
            "Una sucursal o filial tiene que tener una empresa padre. Si es "
            "independiente, márquela como casa matriz."
        )


def _validar_padre(empresa_padre_id: int | None, empresa_id: int | None = None) -> None:
    if empresa_padre_id is None:
        return

    if empresa_padre_id == empresa_id:
        raise ValidationError("Una empresa no puede ser su propia matriz.")

    if repo.obtener(empresa_padre_id) is None:
        raise ValidationError(f"No existe la empresa {empresa_padre_id}.")

    if empresa_id is None:
        return

    # Subir por la cadena: si aparece la propia empresa, es un ciclo.
    visitados = set()
    actual = empresa_padre_id
    while actual is not None:
        if actual == empresa_id:
            raise ValidationError(
                "Ese cambio crearía un ciclo en la jerarquía: la empresa "
                "quedaría siendo descendiente de sí misma."
            )
        if actual in visitados:
            break
        visitados.add(actual)
        padre = repo.obtener(actual)
        actual = padre.empresa_padre_id if padre else None


def _validar_identificacion(
    ident_tributaria: str,
    pais_id: int,
    empresa_padre_id: int | None,
    excluir_id: int | None = None,
) -> None:
    if empresa_padre_id is not None:
        # Es sucursal o filial: en Bolivia comparte el NIT de su matriz.
        return

    if repo.existe_matriz_con_identificacion(ident_tributaria, pais_id, excluir_id):
        raise ValidationError(
            f"Ya hay una casa matriz en ese país con la identificación "
            f"'{ident_tributaria}'. Sería el mismo contribuyente cargado dos veces."
        )


def _obtener_o_fallar(empresa_id: int) -> Empresa:
    empresa = repo.obtener(empresa_id)
    if empresa is None:
        raise ValidationError(f"No existe la empresa {empresa_id}.")
    return empresa


@transaction.atomic
def crear(
    *,
    ident_tributaria: str,
    razon_social: str,
    tipo_empresa_id: int,
    rubro_id: int,
    estado_id: int,
    idioma_default_id: int,
    moneda_oficial_id: int,
    pais_id: int,
    nombre_comercial: str = "",
    empresa_padre_id: int | None = None,
    ubicacion_geografica_id: int | None = None,
) -> Empresa:
    """Da de alta una empresa Y su primer país, en una sola transacción.

    Ni `pais_id` ni `moneda_oficial_id` son columnas de `Empresa`: viven en
    sus tablas puente y se piden acá porque una empresa sin país no se puede
    facturar y sin moneda base no calcula ningún `montoBase`. Postgres no
    puede exigir una fila en OTRA tabla; lo exige esta transacción.
    """
    from comun.empresas.services import empresa_moneda as svc_moneda
    from comun.empresas.services import empresa_pais as svc_pais

    _validar_tipologias(tipo_empresa_id, rubro_id, estado_id)
    _validar_coherencia_jerarquia(tipo_empresa_id, empresa_padre_id)
    _validar_padre(empresa_padre_id)
    _validar_identificacion(ident_tributaria, pais_id, empresa_padre_id)

    empresa = repo.crear(
        ident_tributaria=ident_tributaria,
        razon_social=razon_social,
        nombre_comercial=nombre_comercial,
        tipo_empresa_id=tipo_empresa_id,
        rubro_id=rubro_id,
        estado_id=estado_id,
        idioma_default_id=idioma_default_id,
        empresa_padre_id=empresa_padre_id,
        ubicacion_geografica_id=ubicacion_geografica_id,
    )

    svc_pais.agregar(empresa_id=empresa.pk, pais_id=pais_id)
    svc_moneda.agregar(
        empresa_id=empresa.pk,
        moneda_id=moneda_oficial_id,
        es_moneda_oficial=True,
    )

    return empresa


@transaction.atomic
def actualizar(
    empresa_id: int,
    *,
    ident_tributaria: str | None = None,
    razon_social: str | None = None,
    nombre_comercial: str | None = None,
    tipo_empresa_id: int | None = None,
    rubro_id: int | None = None,
    estado_id: int | None = None,
    idioma_default_id: int | None = None,
    empresa_padre_id: int | None = None,
    ubicacion_geografica_id: int | None = None,
) -> Empresa:
    """El `pais` no se actualiza acá: tiene su propio agregado."""
    empresa = _obtener_o_fallar(empresa_id)

    _validar_tipologias(tipo_empresa_id, rubro_id, estado_id)

    tipo_final = tipo_empresa_id or empresa.tipo_empresa_id
    padre_final = (
        empresa_padre_id if empresa_padre_id is not None else empresa.empresa_padre_id
    )

    if tipo_empresa_id is not None or empresa_padre_id is not None:
        _validar_coherencia_jerarquia(tipo_final, padre_final)
        _validar_padre(padre_final, empresa_id=empresa_id)

    campos = {
        campo: valor
        for campo, valor in (
            ("ident_tributaria", ident_tributaria),
            ("razon_social", razon_social),
            ("nombre_comercial", nombre_comercial),
            ("tipo_empresa_id", tipo_empresa_id),
            ("rubro_id", rubro_id),
            ("estado_id", estado_id),
            ("idioma_default_id", idioma_default_id),
            ("empresa_padre_id", empresa_padre_id),
            ("ubicacion_geografica_id", ubicacion_geografica_id),
        )
        if valor is not None
    }
    if not campos:
        return empresa

    return repo.actualizar(empresa, **campos)


@transaction.atomic
def desactivar(empresa_id: int) -> Empresa:
    """Soft delete. Las sucursales activas se dan de baja una por una y a
    propósito: desactivar veinte empresas con un click es demasiado poder
    para un solo botón.
    """
    empresa = _obtener_o_fallar(empresa_id)

    inactiva = tipologias.obtener_del_sistema(
        AGRUPADOR.ESTADO_EMPRESA, NOMBRE_ESTADO_INACTIVA
    )
    if inactiva is None:
        raise ValidationError(
            f"Falta la tipología '{NOMBRE_ESTADO_INACTIVA}' del agrupador "
            f"ESTADO_EMPRESA. Ejecute: python manage.py cargar_semillas"
        )

    activas = [
        s for s in repo.listar_sucursales_de(empresa_id) if s.estado_id != inactiva.pk
    ]
    if activas:
        nombres = ", ".join(s.razon_social for s in activas[:3])
        raise ValidationError(
            f"No se puede desactivar: tiene {len(activas)} sucursal(es) activa(s) "
            f"({nombres}). Hay que darlas de baja primero."
        )

    return repo.actualizar(empresa, estado_id=inactiva.pk)


def matriz_de(empresa_id: int) -> Empresa | None:
    """La casa matriz de una empresa. Si ya es matriz, se devuelve ella.

    Lleva tope por si un ciclo entrara por una carga manual.
    """
    empresa = repo.obtener(empresa_id)
    if empresa is None:
        return None

    visitados = {empresa.pk}
    while empresa.empresa_padre_id is not None:
        if empresa.empresa_padre_id in visitados:
            break
        padre = repo.obtener(empresa.empresa_padre_id)
        if padre is None:
            break
        visitados.add(padre.pk)
        empresa = padre

    return empresa


def descendientes_de(empresa_id: int) -> list[Empresa]:
    """La empresa y todo lo que cuelga de ella, a cualquier profundidad.

    NO es lo mismo que `ids_del_ambito`: aquel va HACIA ARRIBA y sirve
   para heredar CONFIGURACIÓN; éste baja, y es para operar sobre el grupo
   entero. Devuelve una LISTA de empresas y cada operación se hace parada
   en cada una: el filtro de `TenantManager` no se toca.
   """
    raiz = repo.obtener(empresa_id)
    if raiz is None:
        return []

    encontradas = [raiz]
    visitados = {raiz.pk}
    nivel = [raiz.pk]

    while nivel:
        hijas = [
            h for h in repo.listar_sucursales_de_varias(nivel) if h.pk not in visitados
        ]
        if not hijas:
            break
        for h in hijas:
            visitados.add(h.pk)
        encontradas.extend(hijas)
        nivel = [h.pk for h in hijas]

    return encontradas


def ids_del_ambito(empresa_id: int) -> list[int]:
    """Los ids cuya CONFIGURACIÓN ve esta empresa: ella y su matriz.

        DATOS         (ventas, stock)  → filtro EXACTO, no se comparten
        CONFIGURACIÓN (catálogos)      → se hereda de la matriz

    Esto NO se usa en `TenantManager`. Solo en la configuración.
    """
    matriz = matriz_de(empresa_id)
    if matriz is None:
        return [empresa_id]
    if matriz.pk == empresa_id:
        return [empresa_id]
    return [empresa_id, matriz.pk]


def exigir_del_grupo(empresa_id: int) -> int:
    """El id pedido, solo si es del grupo del cliente de la sesión.

    `Empresa` no puede tener el filtro de tenancy —un `empresa_id` que
    apunta a sí misma no filtra nada—, así que la comprobación se escribe
    acá y la llaman las consultas que reciben un id de afuera.

    El mismo mensaje que si no existiera: decir "no tiene permiso sobre la
    empresa 7" confirma que el 7 existe, y probando números se arma el
    padrón de clientes del SaaS.
    """
    de_la_sesion = empresa_actual()
    if de_la_sesion is None:
        raise ValidationError("No hay empresa en la sesión.")

    mia = matriz_de(de_la_sesion)
    suya = matriz_de(empresa_id)
    if mia is None or suya is None or mia.pk != suya.pk:
        raise ValidationError(f"No existe la empresa {empresa_id}.")

    return empresa_id
