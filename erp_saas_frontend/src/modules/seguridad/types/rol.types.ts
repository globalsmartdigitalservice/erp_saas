export type Rol = {
  id: string;
  nombre: string;
  estadoId: string;
  esHeredado: boolean;
  cantidadPermisos: number | null;
};

/** Lo que se sabe del rol fuera de la lista: el conteo solo lo trae ella. */
export type RolSinConteo = Omit<Rol, "cantidadPermisos">;

export type PermisoDelRol = {
  authPermissionId: string;
  codigo: string;
  etiqueta: string;
};

export type PermisoDeCatalogo = PermisoDelRol & {
  pantalla: string | null;
  modulo: string | null;
};

/** El código sin la app de Django, que es la misma para todos. */
export function codenameDe(permiso: PermisoDelRol): string {
  const partes = permiso.codigo.split(".");
  return partes[partes.length - 1];
}

/**
 * Bajo qué título se agrupa un permiso.
 *
 * Mientras el catálogo de módulos no esté sembrado, `pantalla` llega vacía y
 * queda el prefijo del código, que se arma como `modulo_pantalla_operacion`.
 * Un recurso con más de dos palabras cae en un grupo de nombre raro, no en un
 * error.
 */
export function grupoDePermiso(permiso: PermisoDeCatalogo): string {
  if (permiso.pantalla) return permiso.pantalla;

  return codenameDe(permiso).split("_").slice(0, 2).join("_");
}
