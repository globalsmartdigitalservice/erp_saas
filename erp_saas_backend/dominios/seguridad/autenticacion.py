"""El backend de autenticación del ERP. Hace dos cosas:

    1. que `user.has_perm()` diga la VERDAD en un sistema multiempresa
    2. dejar entrar por nombre de usuario O por correo

`ModelBackend` resuelve los permisos contra `auth_group`, y nosotros los
guardamos en `Grupo_Empresa_Permiso` porque los de Django no tienen
empresa. Sin este backend, `has_perm()` mira el lugar equivocado **y no da
error: devuelve `False` en silencio**.

Vive en `dominios/seguridad/` y no en `core/` porque necesita
`Grupo_Empresa_Permiso`, que es CAPA 4."""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from core.tenancy import empresa_actual

UserModel = get_user_model()


class BackendDeEmpresa(ModelBackend):
    """Los permisos salen de los roles que la persona tiene EN LA EMPRESA
    ACTIVA: la misma persona puede ser cajera en el gimnasio y gerenta en la
    farmacia."""

    # ── 1. Los permisos ────────────────────────────────────────────

    def get_all_permissions(self, user_obj, obj=None):
        """SE SOBRESCRIBE POR EL CACHÉ. `ModelBackend` lo guarda en
        `user_obj._perm_cache`, un atributo que no sabe de empresas: al cambiar de
        sucursal devolvería los permisos de la anterior, sin error.

        Hay que sobrescribir ESTE y no solo `get_group_permissions`: Django cachea
        en los dos niveles."""
        if not user_obj.is_active or user_obj.is_anonymous or obj is not None:
            return set()

        # `None` es una clave válida: es "todavía no eligió empresa", y su
        # respuesta —conjunto vacío— también conviene cachearla.
        empresa_id = empresa_actual()

        cache = getattr(user_obj, self._ATRIBUTO_CACHE, None)
        if cache is None:
            cache = {}
            setattr(user_obj, self._ATRIBUTO_CACHE, cache)

        if empresa_id not in cache:
            cache[empresa_id] = {
                *self.get_user_permissions(user_obj),
                *self.get_group_permissions(user_obj),
            }
        return cache[empresa_id]

    _ATRIBUTO_CACHE = "_permisos_por_empresa"

    def get_group_permissions(self, user_obj, obj=None):
        """Reemplaza el de Django, que lee `auth_group`. Se sobrescribe ESTE y
        no `get_user_permissions` para que aquel siga siendo el de Django."""
        if obj is not None:
            # Permisos por objeto: Django no los implementa y nosotros
            # tampoco. Devolver algo acá sería mentir.
            return set()

        if not user_obj.is_active or user_obj.is_anonymous:
            return set()

        if user_obj.is_superuser or user_obj.is_staff:
            #     is_staff = False  → CLIENTE   → Grupo_Empresa_Permiso
            #     is_staff = True   → PROVEEDOR → auth_group
            #
            # `auth_group` sirve para el proveedor porque su nombre es único
            # en toda la instalación: con un solo proveedor está bien, con
            # 200 clientes era el problema.
            #
            # `is_staff` significa dos cosas: para Django "entra al admin",
            # acá además "es del proveedor". No chocan mientras el admin siga
            # apagado en producción.
            return super().get_group_permissions(user_obj, obj)

        if empresa_actual() is None:
            # Entre el login y el selector no hay permisos que dar. Vacío
            # y no error: preguntar en ese momento es legítimo.
            return set()

        return self._permisos_en_la_empresa(user_obj)

    def _permisos_en_la_empresa(self, user_obj) -> set[str]:
        """Los imports van adentro porque Django carga este módulo antes de que
        el registro de apps esté listo."""
        from comun.membresias import api as membresias
        from dominios.seguridad import api as seguridad

        membresia = membresias.membresia_de(user_obj.pk)
        if membresia is None:
            # Autenticada pero no trabaja en esta empresa. No es error:
            # pasa si manipulan el id de empresa de la sesión.
            return set()

        return seguridad.permisos_de(membresia.pk)

    # ── 3. Entrar por usuario o por correo ─────────────────────────

    def authenticate(self, request, username=None, password=None, **kwargs):
        """Se entra por nombre de usuario o por correo: los dos son únicos."""
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD) or kwargs.get("email")
        if username is None or password is None:
            return None

        usuario = self._buscar(username)

        if usuario is None:
            # NO devolver sin hashear: si el caso "no existe" respondiera
            # al instante, midiendo el tiempo se averigua qué correos están
            # registrados.
            UserModel().set_password(password)
            return None

        if usuario.check_password(password) and self.user_can_authenticate(usuario):
            return usuario
        return None

    def _buscar(self, texto: str):
        """Si el texto coincide con el usuario de UNA persona y el correo de
        OTRA, no entra nadie: elegir sería dejar entrar a la cuenta equivocada."""
        por_usuario = UserModel._default_manager.filter(username=texto).first()
        por_correo = UserModel._default_manager.filter(email__iexact=texto).first()

        if por_usuario and por_correo and por_usuario.pk != por_correo.pk:
            return None

        return por_usuario or por_correo


__all__ = ["BackendDeEmpresa"]
