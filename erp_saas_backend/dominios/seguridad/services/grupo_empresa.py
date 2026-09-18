from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db import transaction

from comun.empresas import api as empresas
from comun.tipologias import api as tipologias
from comun.tipologias.constantes import AGRUPADOR, NOMBRE_ESTADO_BAJA
from core.tenancy import empresa_actual
from dominios.seguridad.models import GrupoEmpresa
from dominios.seguridad.repository import grupo_empresa as repo
from dominios.seguridad.repository import grupo_usuario as repo_asig


def _validar_estado(estado_id: int) -> None:
    tipologias.exigir_del_agrupador(
        estado_id, AGRUPADOR.ESTADO_REGISTRO, "estado del registro"
    )


def _validar_nombre(nombre: str, excluir_id: int | None = None) -> None:
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValidationError("El nombre del rol no puede ir vacío.")

    homonimo = repo.rol_homonimo_en_rama(nombre, excluir_id)
    if homonimo is not None:
        raise ValidationError(_choque(homonimo, nombre))


def _choque(homonimo, nombre: str) -> str:
    """El mensaje dice qué hacer, y eso depende de quién sea el dueño.

    A la matriz se le nombra la sucursal: es su propia organización y sin el
    nombre no sabe a quién pedirle el cambio."""
    if homonimo.empresa_id == empresa_actual():
        return f"Ya tiene un rol llamado '{nombre}'."

    if homonimo.empresa_id in _ids_de_arriba():
        return (
            f"Ya puede usar un rol llamado '{nombre}'. Si es el de su casa "
            f"matriz, asígnelo directamente en vez de crear otro igual."
        )

    return (
        f"La sucursal {homonimo.empresa} ya tiene un rol llamado "
        f"'{nombre}'. Elija otro nombre o pídale que renombre el suyo."
    )


def _ids_de_arriba() -> list[int]:
    return empresas.ids_del_ambito(empresa_actual())


def _exigir_que_sea_propio(grupo: GrupoEmpresa) -> None:
    """
    El invariante 4. El mensaje dice qué hacer, no solo que no se puede.
    """
    if grupo.empresa_id != empresa_actual():
        raise ValidationError(
            f"El rol '{grupo.nombre}' es de su casa matriz y solo ella puede "
            f"modificarlo: si lo cambiara, les cambiaría los permisos a "
            f"todas las sucursales del grupo. Si necesita algo distinto, "
            f"cree un rol propio."
        )


@transaction.atomic
def crear(*, nombre: str, estado_id: int) -> GrupoEmpresa:
    """
    El rol se crea SIEMPRE en la empresa activa.

     `empresa` no se recibe por parámetro a propósito: si viniera de
    afuera, alguien podría crear un rol dentro de otra empresa mandando
    un id. Sale del contexto, que es del lado del servidor.
    """
    _validar_estado(estado_id)
    nombre = (nombre or "").strip()
    _validar_nombre(nombre)

    return repo.crear(empresa_id=empresa_actual(), nombre=nombre, estado_id=estado_id)


@transaction.atomic
def actualizar(
    grupo_id: int, *, nombre: str | None = None, estado_id: int | None = None
) -> GrupoEmpresa:
    grupo = repo.obtener(grupo_id)
    if grupo is None:
        raise ValidationError(f"No existe el rol {grupo_id}.")

    _exigir_que_sea_propio(grupo)

    if estado_id is not None:
        _validar_estado(estado_id)

    if nombre is not None:
        nombre = nombre.strip()
        _validar_nombre(nombre, excluir_id=grupo_id)

    campos = {
        campo: valor
        for campo, valor in (("nombre", nombre), ("estado_id", estado_id))
        if valor is not None
    }
    if not campos:
        return grupo

    return repo.actualizar(grupo, **campos)


@transaction.atomic
def desactivar(grupo_id: int) -> GrupoEmpresa:
    """
    Soft delete, con una condición: **no se da de baja un rol que alguien
    todavía tiene**.

    Si se pudiera, esas personas perderían sus permisos de golpe y el
    mensaje que verían sería "no tenés permiso", sin ninguna pista de por
    qué. El mensaje de acá dice qué hay que hacer primero.
    """
    grupo = repo.obtener(grupo_id)
    if grupo is None:
        raise ValidationError(f"No existe el rol {grupo_id}.")

    _exigir_que_sea_propio(grupo)

    if repo_asig.hay_asignaciones_de_grupo(grupo_id):
        raise ValidationError(
            f"No se puede dar de baja '{grupo.nombre}': hay gente que lo tiene "
            f"asignado. Quitáselo primero a esas personas."
        )

    baja = tipologias.obtener_del_sistema(
        AGRUPADOR.ESTADO_REGISTRO, NOMBRE_ESTADO_BAJA
    )
    if baja is None:
        raise ValidationError(
            f"Falta la tipología '{NOMBRE_ESTADO_BAJA}' del agrupador "
            f"ESTADO_REGISTRO. Ejecute: python manage.py cargar_semillas"
        )

    return repo.actualizar(grupo, estado_id=baja.pk)


@transaction.atomic
def agregar_permiso(*, grupo_id: int, auth_permission_id: int):
    """
    Le da un permiso a un rol. Idempotente: darlo dos veces no falla ni
    duplica — quien arma un rol marcando casillas no tiene por qué saber
    si ya estaba.
    """
    grupo = repo.obtener(grupo_id)
    if grupo is None:
        raise ValidationError(f"No existe el rol {grupo_id}.")

    _exigir_que_sea_propio(grupo)

    if not Permission.objects.filter(pk=auth_permission_id).exists():
        raise ValidationError(f"No existe el permiso {auth_permission_id}.")

    if repo.existe_permiso_en(grupo_id, auth_permission_id):
        return repo.listar_permisos_de(grupo_id)

    repo.agregar_permiso(grupo_id, auth_permission_id)
    return repo.listar_permisos_de(grupo_id)


@transaction.atomic
def quitar_permiso(*, grupo_id: int, auth_permission_id: int):
    """Idempotente también: quitar lo que no estaba no es un error."""
    grupo = repo.obtener(grupo_id)
    if grupo is None:
        raise ValidationError(f"No existe el rol {grupo_id}.")

    _exigir_que_sea_propio(grupo)

    repo.quitar_permiso(grupo_id, auth_permission_id)
    return repo.listar_permisos_de(grupo_id)
