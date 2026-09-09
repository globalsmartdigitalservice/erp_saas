import { gql } from "@apollo/client";


export const SESION_ACTUAL = gql`
  query SesionActual {
    yo {
      id
      nombreCompleto
    }
    miEmpresa {
      empresaId
      razonSocial
      esMatriz
    }
    misPermisos
  }
`;
