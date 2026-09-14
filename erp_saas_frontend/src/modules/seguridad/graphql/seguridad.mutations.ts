import { gql } from "@apollo/client";

/**
 * Ninguna de las dos devuelve los tokens: viajan en cookies HttpOnly que el
 * navegador guarda y manda solo. El frontend nunca los ve ni los toca.
 */

export const LOGIN = gql`
  mutation Login($datos: LoginInput!) {
    login(datos: $datos) {
      necesitaElegirEmpresa
      usuario {
        id
        nombreCompleto
      }
      empresas {
        membresiaId
        empresaId
        razonSocial
        esMatriz
      }
    }
  }
`;

export const ELEGIR_EMPRESA = gql`
  mutation ElegirEmpresa($datos: LoginInput!, $empresaId: ID!) {
    elegirEmpresa(datos: $datos, empresaId: $empresaId) {
      necesitaElegirEmpresa
      usuario {
        id
        nombreCompleto
      }
    }
  }
`;

/** Cierra la sesión en el backend, que además borra las dos cookies. */
export const LOGOUT = gql`
  mutation Logout {
    logout
  }
`;
