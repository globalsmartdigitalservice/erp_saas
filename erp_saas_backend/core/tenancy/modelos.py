

from django.db import models

from .contexto import empresa_actual, filtro_desactivado
from .managers import TenantDerivadoManager, TenantManager


class ModeloTenant(models.Model):

    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.PROTECT,
        related_name="+",
        db_index=True,
        editable=False,
    )

    objects = TenantManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
   
        if self.empresa_id is None:
            self.empresa_id = empresa_actual()
        super().save(*args, **kwargs)


class PadreDeOtraEmpresa(RuntimeError):
    """
    Se intentó colgar una fila de un padre que no es de la empresa activa.

    No es un error de validación de negocio: es un intento de escribir en
    los datos de otro cliente. Por eso sube como error, no como mensaje.
    """


class ModeloTenantDerivado(models.Model):
 

    RUTA_A_EMPRESA: str = ""

    objects = TenantDerivadoManager()

    class Meta:
        abstract = True

 

    @classmethod
    def from_db(cls, db, field_names, values):
        fila = super().from_db(db, field_names, values)
        fila._padre_original = fila._padre_id()
        return fila

    def _padre_id(self):
        """El id del PRIMER salto de la ruta: la FK que esta fila guarda."""
        if not self.RUTA_A_EMPRESA:
            return None
        primer_salto = self.RUTA_A_EMPRESA.split("__")[0]
        return getattr(self, self._meta.get_field(primer_salto).attname, None)

    def _padre_es_visible(self) -> bool:
        primer_salto = self.RUTA_A_EMPRESA.split("__")[0]
        campo = self._meta.get_field(primer_salto)
        padre_id = getattr(self, campo.attname, None)

        if padre_id is None:
            
            return True

   
        return campo.related_model.objects.filter(pk=padre_id).exists()

    def save(self, *args, **kwargs):
        cambio_de_padre = (
            self._state.adding
            or self._padre_id() != getattr(self, "_padre_original", None)
        )

        if cambio_de_padre and not filtro_desactivado() and self.RUTA_A_EMPRESA:
            if not self._padre_es_visible():
                salto = self.RUTA_A_EMPRESA.split("__")[0]
                raise PadreDeOtraEmpresa(
                    f"El {salto} al que se cuelga este {type(self).__name__} "
                    f"no es de la empresa activa. Resolvé la FK contra el "
                    f"queryset ya filtrado, nunca por id "
                    f"crudo."
                )

        super().save(*args, **kwargs)
        self._padre_original = self._padre_id()
