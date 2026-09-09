"""
Acceso a datos de `Usuario`.

 SIN FILTRO DE EMPRESA, y no es un olvido: es identidad GLOBAL. Juan es
la misma persona en el gimnasio y en la farmacia.

Eso NO significa que cualquiera pueda listar a todos los usuarios del
SaaS: la pantalla "usuarios de mi empresa" no sale de acá, sale de
`comun/membresias`, que sí filtra. Lo de acá se usa para resolver a una
persona que ya se sabe cuál es —el login, el alta— y para leer sus datos.
"""

from django.contrib.auth import get_user_model

Usuario = get_user_model()


def obtener(usuario_id: int) -> "Usuario | None":
    return Usuario.objects.filter(pk=usuario_id).first()


def obtener_varios(usuario_ids) -> dict[int, "Usuario"]:
    """
    Versión por lote. OBLIGATORIA.

    Acá pesa más que en otras apps: la lista de usuarios de una empresa
    sale de `membresias`, y sin esto cada fila dispararía una consulta
    para mostrar el nombre de la persona.
    """
    return {u.pk: u for u in Usuario.objects.filter(pk__in=list(usuario_ids))}


def obtener_por_username(username: str) -> "Usuario | None":
    return Usuario.objects.filter(username=username).first()


def obtener_por_email(email: str) -> "Usuario | None":
    """Sin distinguir mayúsculas: nadie escribe su correo igual dos veces."""
    return Usuario.objects.filter(email__iexact=email).first()


def existe_username(username: str, excluir_id: int | None = None) -> bool:
    qs = Usuario.objects.filter(username=username)
    if excluir_id is not None:
        qs = qs.exclude(pk=excluir_id)
    return qs.exists()


def existe_email(email: str, excluir_id: int | None = None) -> bool:
    qs = Usuario.objects.filter(email__iexact=email)
    if excluir_id is not None:
        qs = qs.exclude(pk=excluir_id)
    return qs.exists()


def crear(**campos) -> "Usuario":
    """
    Va por `create_user` y NO por `objects.create`, a propósito: el
    primero hashea la contraseña y el segundo la guardaría EN CLARO.
    """
    password = campos.pop("password")
    return Usuario.objects.create_user(password=password, **campos)


def actualizar(usuario: "Usuario", **campos) -> "Usuario":
    for campo, valor in campos.items():
        setattr(usuario, campo, valor)
    usuario.save(update_fields=list(campos))
    return usuario
