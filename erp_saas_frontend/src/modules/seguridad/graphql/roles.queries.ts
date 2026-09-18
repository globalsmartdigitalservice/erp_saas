import { gql } from "@apollo/client";

export const ROLES = gql`
  query Roles($estadoId: ID) {
    roles(estadoId: $estadoId) {
      id
      nombre
      estadoId
      esHeredado
      cantidadPermisos
    }
  }
`;

// Sin `cantidadPermisos`: acá viaja en null y pisaría en la caché el conteo
// que trajo la lista.
export const DETALLE_ROL = gql`
  query DetalleRol($id: ID!) {
    rol(id: $id) {
      id
      nombre
      estadoId
      esHeredado
    }
  }
`;

export const PERMISOS_DEL_ROL = gql`
  query PermisosDelRol($rolId: ID!) {
    permisosDelRol(rolId: $rolId) {
      authPermissionId
      codigo
      etiqueta
    }
  }
`;

export const CATALOGO_DE_PERMISOS = gql`
  query CatalogoDePermisos {
    catalogoDePermisos {
      authPermissionId
      codigo
      etiqueta
      pantalla
      modulo
    }
  }
`;
