import { gql } from "@apollo/client";

export const DAR_DE_ALTA_MIEMBRO = gql`
  mutation DarDeAltaMiembro($datos: DarDeAltaMiembroInput!) {
    darDeAltaMiembro(datos: $datos) {
      membresia {
        id
        usuario {
          id
          username
          nombreCompleto
        }
      }
      passwordTemporal
    }
  }
`;

export const ACTUALIZAR_USUARIO = gql`
  mutation ActualizarUsuario($id: ID!, $datos: ActualizarUsuarioInput!) {
    actualizarUsuario(id: $id, datos: $datos) {
      id
    }
  }
`;

export const RESETEAR_PASSWORD = gql`
  mutation ResetearPassword($datos: ResetearPasswordInput!) {
    resetearPassword(datos: $datos)
  }
`;

export const DESAFILIAR = gql`
  mutation Desafiliar($datos: DesafiliarInput!) {
    desafiliar(datos: $datos) {
      id
    }
  }
`;

export const REACTIVAR_MEMBRESIA = gql`
  mutation ReactivarMembresia($membresiaId: ID!, $estadoActivoId: ID!) {
    reactivarMembresia(membresiaId: $membresiaId, estadoActivoId: $estadoActivoId) {
      id
    }
  }
`;

export const DESACTIVAR_USUARIO = gql`
  mutation DesactivarUsuario($id: ID!) {
    desactivarUsuario(id: $id) {
      id
    }
  }
`;

export const REACTIVAR_USUARIO = gql`
  mutation ReactivarUsuario($id: ID!) {
    reactivarUsuario(id: $id) {
      id
    }
  }
`;

export const ASIGNAR_ROL = gql`
  mutation AsignarRol($datos: AsignarRolInput!) {
    asignarRol(datos: $datos) {
      id
    }
  }
`;

export const QUITAR_ROL = gql`
  mutation QuitarRol($asignacionId: ID!) {
    quitarRol(asignacionId: $asignacionId) {
      id
    }
  }
`;
