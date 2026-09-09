"""Los tipos de usuarios que ve el frontend. Sin lógica: solo forma."""

import strawberry


@strawberry.type(name="Usuario")
class UsuarioType:
    """
    Una persona del sistema.

     NO EXPONE `password` NI SU HASH, y no es un descuido. El hash no le
    sirve a ninguna pantalla y publicarlo le regala a un atacante el
    material para probar contraseñas sin límite y sin dejar rastro en
    ningún log.

    Tampoco expone `is_superuser`: quién es staff del proveedor no es
    asunto de los clientes.
    """

    id: strawberry.ID
    username: str
    email: str
    first_name: str
    last_name: str
    seg_apellido: str
    nombre_completo: str
    is_active: bool
    debe_cambiar_password: bool

    @classmethod
    def desde_modelo(cls, usuario) -> "UsuarioType":
        return cls(
            id=strawberry.ID(str(usuario.pk)),
            username=usuario.username,
            email=usuario.email,
            first_name=usuario.first_name,
            last_name=usuario.last_name,
            seg_apellido=usuario.seg_apellido,
            # Se manda armado y no se calcula en el frontend: el orden de
            # los apellidos es una regla del dominio, no de la pantalla.
            nombre_completo=usuario.get_full_name(),
            is_active=usuario.is_active,
            debe_cambiar_password=usuario.debe_cambiar_password,
        )
