import { gql } from "@apollo/client";

/**
 * Ninguna de las dos devuelve los tokens: viajan en cookies HttpOnly que el
 * navegador guarda y manda solo. El frontend nunca los ve ni los toca.
 */

export const INGRESAR = gql`
  mutation Ingresar($datos: IngresarInput!) {
    ingresar(datos: $datos) {
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
  mutation ElegirEmpresa($datos: IngresarInput!, $empresaId: ID!) {
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
export const SALIR = gql`
  mutation Salir {
    salir
  }
`;
