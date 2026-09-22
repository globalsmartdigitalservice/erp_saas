import { gql } from "@apollo/client";

export const IDIOMAS_ACTIVOS = gql`
  query IdiomasActivos {
    idiomas(soloActivos: true) {
      id
      codigo
      nombre
    }
  }
`;
