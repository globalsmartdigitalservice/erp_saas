import { gql } from "@apollo/client";

export const CREAR_ENTIDAD = gql`
  mutation CrearEntidad($datos: CrearEntidadInput!) {
    crearEntidad(datos: $datos) {
      id
      nombre
    }
  }
`;

export const ACTUALIZAR_ENTIDAD = gql`
  mutation ActualizarEntidad($id: ID!, $datos: ActualizarEntidadInput!) {
    actualizarEntidad(id: $id, datos: $datos) {
      id
      nombre
    }
  }
`;

export const DESACTIVAR_ENTIDAD = gql`
  mutation DesactivarEntidad($id: ID!) {
    desactivarEntidad(id: $id) {
      id
      estado {
        nombre
      }
    }
  }
`;

export const CREAR_ROL = gql`
  mutation CrearRolEntidad($datos: CrearRolEntidadInput!) {
    crearRolEntidad(datos: $datos) {
      id
    }
  }
`;

export const ACTUALIZAR_ROL = gql`
  mutation ActualizarRolEntidad(
    $id: ID!
    $datos: ActualizarRolEntidadInput!
  ) {
    actualizarRolEntidad(id: $id, datos: $datos) {
      id
    }
  }
`;

export const DESACTIVAR_ROL = gql`
  mutation DesactivarRolEntidad($id: ID!) {
    desactivarRolEntidad(id: $id) {
      id
    }
  }
`;

export const CREAR_DIRECCION = gql`
  mutation CrearDireccion($datos: CrearDireccionInput!) {
    crearDireccion(datos: $datos) {
      id
    }
  }
`;

export const ACTUALIZAR_DIRECCION = gql`
  mutation ActualizarDireccion($id: ID!, $datos: ActualizarDireccionInput!) {
    actualizarDireccion(id: $id, datos: $datos) {
      id
    }
  }
`;

export const DESACTIVAR_DIRECCION = gql`
  mutation DesactivarDireccion($id: ID!) {
    desactivarDireccion(id: $id) {
      id
    }
  }
`;

export const CREAR_CONTACTO = gql`
  mutation CrearContactoEntidad($datos: CrearContactoEntidadInput!) {
    crearContactoEntidad(datos: $datos) {
      id
    }
  }
`;

export const ACTUALIZAR_CONTACTO = gql`
  mutation ActualizarContactoEntidad(
    $id: ID!
    $datos: ActualizarContactoEntidadInput!
  ) {
    actualizarContactoEntidad(id: $id, datos: $datos) {
      id
    }
  }
`;

export const DESACTIVAR_CONTACTO = gql`
  mutation DesactivarContactoEntidad($id: ID!) {
    desactivarContactoEntidad(id: $id) {
      id
      estado {
        nombre
      }
    }
  }
`;

export const CREAR_CATEGORIA = gql`
  mutation CrearCategoriaEntidad($datos: CrearCategoriaEntidadInput!) {
    crearCategoriaEntidad(datos: $datos) {
      id
      nombre
    }
  }
`;

export const ACTUALIZAR_CATEGORIA = gql`
  mutation ActualizarCategoriaEntidad(
    $id: ID!
    $datos: ActualizarCategoriaEntidadInput!
  ) {
    actualizarCategoriaEntidad(id: $id, datos: $datos) {
      id
      nombre
    }
  }
`;

export const DESACTIVAR_CATEGORIA = gql`
  mutation DesactivarCategoriaEntidad($id: ID!) {
    desactivarCategoriaEntidad(id: $id) {
      id
      estado {
        nombre
      }
    }
  }
`;
