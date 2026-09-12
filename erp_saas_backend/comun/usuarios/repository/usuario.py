"""
Acceso a datos de `Usuario`.

 Cada cuenta pertenece a un cliente (`matriz`), o a ninguno si es del
proveedor. Juan trabajando en el gimnasio y en la farmacia son DOS
cuentas, y ninguna de las dos se entera de la otra.

Las consultas de acá no llevan filtro por empresa: el login tiene que
encontrar la cuenta antes de saber dónde va a trabajar. Quién puede ver
o tocar a quién lo deciden los services, no esta capa. Y la pantalla
"usuarios de mi empresa" no sale de acá: sale de `comun/membresias`.
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


def existe_email(
    email: str, matriz_id: int | None, excluir_id: int | None = None
) -> bool:
    """Dentro del cliente: el mismo correo puede estar en otro."""
    qs = Usuario.objects.filter(email__iexact=email, matriz_id=matriz_id)
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
