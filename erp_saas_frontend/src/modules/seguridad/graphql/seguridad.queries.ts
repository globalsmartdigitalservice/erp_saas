import { gql } from "@apollo/client";


export const SESION_ACTUAL = gql`
  query SesionActual {
    me {
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
