"""
El que espía la cajita y le agrega el filtro a cada consulta.

Gracias a esto el dev escribe:

    Venta.objects.all()

y la base recibe:

    SELECT * FROM venta WHERE empresa_id = 7

El filtro no se puede olvidar porque no se escribe.
"""

from django.core.exceptions import ImproperlyConfigured
from django.db import models

from .contexto import SinEmpresaEnContexto, empresa_actual, filtro_desactivado


class TenantQuerySet(models.QuerySet):
    """QuerySet normal. Se separa para poder encadenar métodos propios."""


class TenantManager(models.Manager.from_queryset(TenantQuerySet)):
    """
    Manager que inyecta `WHERE empresa_id = <la de la cajita>`.

    El filtro se aplica al CREAR el queryset, no al evaluarlo, para que
    el error salte con el stack trace apuntando a la línea culpable.
    """

    def get_queryset(self):
        qs = super().get_queryset()

   
        if filtro_desactivado():
            return qs

        empresa_id = empresa_actual()
        if empresa_id is None:
            raise SinEmpresaEnContexto(
                f"Se consultó {self.model.__name__} sin empresa en el contexto. "
                f"Si es a propósito, usá `with sin_filtro_de_empresa():`."
            )

        return qs.filter(empresa_id=empresa_id)


class TenantDerivadoManager(models.Manager.from_queryset(TenantQuerySet)):
    """
    El filtro para las tablas que NO llevan `empresa_id` propio.

    En vez de comparar una columna de la tabla, salta al padre siguiendo
    `RUTA_A_EMPRESA`:

        SELECT * FROM ent_direccion
          INNER JOIN ent_entidad ON (...)
         WHERE ent_entidad.empresa_id = 7

    ES LA MISMA GARANTÍA, POR OTRO CAMINO. Lo que no cambia es lo que
    importa: el filtro no se escribe, así que no se puede olvidar.

     Y una diferencia que sí importa: `TenantManager` protege la LECTURA
    y la ESCRITURA —su `save()` rellena `empresa_id` desde el contexto, así
    que es imposible escribir en otra empresa—. Este manager solo protege
    la lectura. La escritura la cierra `ModeloTenantDerivado.save()`,
    comprobando que el padre sea visible.
    """

    def get_queryset(self):
        qs = super().get_queryset()

        if filtro_desactivado():
            return qs

        empresa_id = empresa_actual()
        if empresa_id is None:
            raise SinEmpresaEnContexto(
                f"Se consultó {self.model.__name__} sin empresa en el contexto. "
                f"Si es a propósito, usá `with sin_filtro_de_empresa():`."
            )

        ruta = getattr(self.model, "RUTA_A_EMPRESA", "")
        if not ruta:
            raise ImproperlyConfigured(
                f"{self.model.__name__} hereda de ModeloTenantDerivado y no "
                f"declaró RUTA_A_EMPRESA. Sin esa ruta el filtro no sabe por "
                f"dónde saltar al padre, y la tabla quedaría sin aislar."
            )

        return qs.filter(**{f"{ruta}__empresa_id": empresa_id})
