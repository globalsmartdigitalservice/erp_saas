"""
Acceso a datos de `Usuario_Empresa`.

 ESTA CAPA NO ABRE LA PUERTA DE SALIDA DEL AISLAMIENTO.

Casi todas las consultas de acá corren con el filtro por empresa puesto,
como cualquier otra tabla. Las dos que tienen que cruzar empresas —el
login y el alta en el grupo— dicen en su nombre que lo hacen y lo
declaran a mano con `sin_filtro_de_empresa()`, para que se vea en el
código quién cruzó y por qué.
"""

from comun.membresias.models import UsuarioEmpresa
from core.tenancy import sin_filtro_de_empresa


def obtener(membresia_id: int) -> UsuarioEmpresa | None:
    return UsuarioEmpresa.objects.filter(pk=membresia_id).first()


def obtener_varias(membresia_ids) -> dict[int, UsuarioEmpresa]:
    return {
        m.pk: m for m in UsuarioEmpresa.objects.filter(pk__in=list(membresia_ids))
    }


def listar(estado_id: int | None = None) -> list[UsuarioEmpresa]:
    """
    Quiénes trabajan en la empresa del contexto.

    Recibe el `estado_id` ya resuelto y no un booleano `solo_activas`,
    por lo mismo que en `monedas`: "activa" es una fila de `Tipologia`
    y esta capa no la puede conocer.
    """
    qs = UsuarioEmpresa.objects.select_related("usuario")
    if estado_id is not None:
        qs = qs.filter(estado_id=estado_id)
    return list(qs)


def obtener_de_usuario(usuario_id: int) -> UsuarioEmpresa | None:
    """La membresía de esa persona EN LA EMPRESA DEL CONTEXTO."""
    return (
        UsuarioEmpresa.objects.filter(usuario_id=usuario_id)
        .select_related("empresa")
        .first()
    )


def listar_de_usuario_en_todas_las_empresas(usuario_id: int) -> list[UsuarioEmpresa]:
    """
    TODAS las membresías de una persona, de todas las empresas.

     CRUZA EMPRESAS A PROPÓSITO. Es la consulta del LOGIN: en ese
    momento no hay empresa en el contexto —se la está averiguando—, así
    que el manager levantaría `SinEmpresaEnContexto`.

    Es lo que llena la pantalla "¿dónde querés trabajar?" cuando alguien
    está dado de alta en más de una empresa.
    """
    with sin_filtro_de_empresa():
        return list(
            UsuarioEmpresa.objects.filter(usuario_id=usuario_id).select_related(
                "empresa", "estado"
            )
        )


def listar_de_usuario_con_estado(usuario_id: int, estado_id: int) -> list[UsuarioEmpresa]:
    """Las membresías de una persona en ese estado, en todas las empresas: cruza a propósito."""
    with sin_filtro_de_empresa():
        return list(
            UsuarioEmpresa.objects.filter(usuario_id=usuario_id, estado_id=estado_id)
        )


def existe_en(usuario_id: int, empresa_id: int) -> bool:
    """
    ¿Esta persona ya está dada de alta en ESA empresa?

     CRUZA EMPRESAS: la usa el alta en el grupo, que escribe filas de
    la matriz y de todas sus sucursales de una vez. Sin esto, el
    `unique(usuario, empresa)` respondería con un IntegrityError en vez
    de un mensaje con sentido.
    """
    with sin_filtro_de_empresa():
        return UsuarioEmpresa.objects.filter(
            usuario_id=usuario_id, empresa_id=empresa_id
        ).exists()


def crear_en(
    *,
    usuario_id: int,
    empresa_id: int,
    fecha_asignacion,
    estado_id: int,
) -> UsuarioEmpresa:
    """
    Da de alta a alguien en UNA empresa, dicha explícitamente.

     CRUZA EMPRESAS: la empresa viene por parámetro y no del contexto,
    porque quien afilia está parado en la matriz y escribe filas de las
    sucursales. Quién puede hacerlo lo decide el service, no esta capa.
    """
    with sin_filtro_de_empresa():
        return UsuarioEmpresa.objects.create(
            usuario_id=usuario_id,
            empresa_id=empresa_id,
            fecha_asignacion=fecha_asignacion,
            estado_id=estado_id,
        )
