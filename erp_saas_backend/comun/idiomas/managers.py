

from django.db import models

from core.tenancy import empresa_actual, filtro_desactivado


class TraduccionQuerySet(models.QuerySet):
    def de_fabrica(self):
        """Solo las del proveedor, sin importar la empresa activa."""
        return self.filter(empresa__isnull=True)

    def para(self, entidad_tipo: str, campo: str | None = None):
        """Las de una tabla, y opcionalmente las de un solo campo."""
        qs = self.filter(entidad_tipo=entidad_tipo)
        if campo is not None:
            qs = qs.filter(campo=campo)
        return qs

    def en_idioma(self, idioma_id: int):
        return self.filter(idioma_id=idioma_id)


class TraduccionManager(models.Manager.from_queryset(TraduccionQuerySet)):
    def get_queryset(self):
        qs = super().get_queryset()

        if filtro_desactivado():
            return qs

        empresa_id = empresa_actual()
        if empresa_id is None:
   
            return qs.filter(empresa__isnull=True)

 
        from comun.empresas import api as empresas

     
        ambito = empresas.ids_del_ambito(empresa_id)

        return qs.filter(
            models.Q(empresa_id__in=ambito) | models.Q(empresa__isnull=True)
        )


__all__ = ["TraduccionManager", "TraduccionQuerySet"]
