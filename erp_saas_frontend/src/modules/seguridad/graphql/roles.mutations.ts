import { gql } from "@apollo/client";

export const CREAR_ROL = gql`
  mutation CrearRol($datos: CrearRolInput!) {
    crearRol(datos: $datos) {
      id
      nombre
      estadoId
      esHeredado
      cantidadPermisos
    }
  }
`;

export const ACTUALIZAR_ROL = gql`
  mutation ActualizarRol($id: ID!, $datos: ActualizarRolInput!) {
    actualizarRol(id: $id, datos: $datos) {
      id
      nombre
      estadoId
      esHeredado
      cantidadPermisos
    }
  }
`;

export const DESACTIVAR_ROL = gql`
  mutation DesactivarRol($id: ID!) {
    desactivarRol(id: $id) {
      id
      estadoId
    }
  }
`;

export const AGREGAR_PERMISO_AL_ROL = gql`
  mutation AgregarPermisoAlRol($rolId: ID!, $authPermissionId: ID!) {
    agregarPermisoAlRol(rolId: $rolId, authPermissionId: $authPermissionId) {
      authPermissionId
      codigo
      etiqueta
    }
  }
`;

export const QUITAR_PERMISO_DEL_ROL = gql`
  mutation QuitarPermisoDelRol($rolId: ID!, $authPermissionId: ID!) {
    quitarPermisoDelRol(rolId: $rolId, authPermissionId: $authPermissionId) {
      authPermissionId
      codigo
      etiqueta
    }
  }
`;
