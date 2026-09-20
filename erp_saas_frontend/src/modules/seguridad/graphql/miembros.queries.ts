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

export const DETALLE_MIEMBRO = gql`
  query DetalleMiembro($usuarioId: ID!) {
    usuario(id: $usuarioId) {
      id
      username
      email
      firstName
      lastName
      segApellido
      nombreCompleto
      isActive
      debeCambiarPassword
    }
    membresia(usuarioId: $usuarioId) {
      id
      fechaAsignacion
      fechaFinalizacion
      estadoId
    }
  }
`;

export const ROLES_DE_MIEMBRO = gql`
  query RolesDeMiembro($membresiaId: ID!) {
    rolesDe(membresiaId: $membresiaId) {
      id
      fechaInicio
      fechaFin
      motivo
      estadoId
      rol {
        id
        nombre
        esHeredado
        estadoId
      }
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
