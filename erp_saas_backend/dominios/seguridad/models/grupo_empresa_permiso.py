from django.db import models

from dominios.seguridad.managers import PermisoDeGrupoManager


class GrupoEmpresaPermiso(models.Model):

    grupo_empresa = models.ForeignKey(
        "seguridad.GrupoEmpresa",
        on_delete=models.CASCADE,
        related_name="permisos",
    )


    auth_permission = models.ForeignKey(
        "auth.Permission",
        on_delete=models.PROTECT,
        related_name="+",
    )


    objects = PermisoDeGrupoManager()

    class Meta:
        db_table = "segu_grupo_empresa_permiso"
        verbose_name = "Permiso del rol"
        verbose_name_plural = "Permisos del rol"
        constraints = [
            models.UniqueConstraint(
                fields=["grupo_empresa", "auth_permission"],
                name="permiso_unico_por_rol",
            ),
        ]

    def __str__(self):
        return f"{self.grupo_empresa.nombre}: {self.auth_permission.codename}"
