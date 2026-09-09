from django.db import models


class PermisoDeNegocio(models.Model):
    class Meta:
        
        managed = False
        default_permissions = ()
        verbose_name = "Permiso de negocio"
        verbose_name_plural = "Permisos de negocio"
