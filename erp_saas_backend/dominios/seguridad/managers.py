"""Los dos managers propios del módulo 12.

Ninguna de las dos tablas puede usar el `TenantManager` ni el
`TenantDerivadoManager` estándar, y el motivo cabe en una frase: **un rol
es CONFIGURACIÓN, y la configuración baja de la matriz a las sucursales.**

    la CONFIGURACIÓN baja de la matriz    (catálogos, y ahora los roles)
    los DATOS no bajan                    (ventas, stock: filtro exacto)
    la herencia NO SUBE

Sin esto, una cadena de 20 sucursales definiría "Cajero" veinte veces, y a
los tres meses serían veinte roles distintos con el mismo nombre.

 A diferencia de `TipologiaManager`, acá NO hay filas de fábrica
(`empresa = NULL`) ni ocultamiento: no hay roles de fábrica porque un rol
trae permisos, y qué permisos existen depende de los módulos que el
cliente contrató. Un "Vendedor" de fábrica apuntando a permisos de módulos
que el cliente no tiene es peor que una lista vacía.
"""

from django.db import models

from core.tenancy import SinEmpresaEnContexto, empresa_actual, filtro_desactivado


class GrupoEmpresaManager(models.Manager):
    """Los roles que esta empresa PUEDE USAR: los suyos y los de su matriz.

    Ver no es editar: que la sucursal no toque el rol de la matriz lo valida
    el service."""

    def get_queryset(self):
        qs = super().get_queryset()

        if filtro_desactivado():
            return qs

        # Ella y su matriz: 1-2 búsquedas por clave primaria.
        ambito = self._empresas().ids_del_ambito(self._exigir_empresa())
        return qs.filter(empresa_id__in=ambito)

    def de_rama(self):
        """Ella, su matriz y sus descendientes. Solo para validar nombres.

        El ACOTE vive acá y no en quien consulta: escrito afuera, el día que
        alguien lo olvide la consulta devuelve los roles de todos los
        clientes.
        """
        ids = self._empresas().ids_de_rama(self._exigir_empresa())
        return super().get_queryset().filter(empresa_id__in=ids)

    @staticmethod
    def _empresas():
        # El import va acá adentro: `models` importa este archivo para
        # declarar el manager, y al tope se haría circular.
        from comun.empresas import api as empresas

        return empresas

    @staticmethod
    def _exigir_empresa() -> int:
        empresa_id = empresa_actual()
        if empresa_id is None:
            # Acá SÍ se levanta, a diferencia de `TipologiaManager`:
            # roles de fábrica no hay, así que sin empresa no hay nada que
            # devolver y un queryset vacío sería una respuesta engañosa.
            raise SinEmpresaEnContexto(
                "Se consultó GrupoEmpresa sin empresa en el contexto. "
                "Si es a propósito, usá `with sin_filtro_de_empresa():`."
            )
        return empresa_id


class PermisoDeGrupoManager(models.Manager):
    """Los permisos de los roles que esta empresa ve.

     NO puede ser `ModeloTenantDerivado`: aquel filtra por la empresa del
    padre con igualdad exacta, y con un rol heredado de la matriz la sucursal
    vería el rol con CERO permisos, sin ningún error."""

    def get_queryset(self):
        qs = super().get_queryset()

        if filtro_desactivado():
            return qs

        from dominios.seguridad.models import GrupoEmpresa

        # `GrupoEmpresa.objects` ya levanta `SinEmpresaEnContexto` si no
        # hay empresa, así que no hace falta repetir el chequeo.
        visibles = GrupoEmpresa.objects.values("pk")
        return qs.filter(grupo_empresa_id__in=visibles)


__all__ = ["GrupoEmpresaManager", "PermisoDeGrupoManager"]
