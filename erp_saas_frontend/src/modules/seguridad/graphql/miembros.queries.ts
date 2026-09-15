import { gql } from "@apollo/client";

export const MIEMBROS = gql`
  query Miembros($estadoId: ID) {
    miembros(estadoId: $estadoId) {
      id
      estadoId
      fechaAsignacion
      usuario {
        id
        username
        email
        nombreCompleto
        isActive
        debeCambiarPassword
      }
      roles {
        id
        nombre
      }
    }
  }
`;

export const PERSONA_POR_CORREO = gql`
  query PersonaPorCorreo($email: String!) {
    personaPorCorreo(email: $email) {
      usuarioId
      nombreCompleto
      trabajaAca
    }
  }
`;

export const ROLES_ASIGNABLES = gql`
  query RolesAsignables($estadoId: ID) {
    roles(estadoId: $estadoId) {
      id
      nombre
      esHeredado
    }
  }
`;
