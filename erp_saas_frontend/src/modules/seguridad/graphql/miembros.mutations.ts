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
