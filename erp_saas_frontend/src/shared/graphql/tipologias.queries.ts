import { gql } from "@apollo/client";


export const AGRUPADORES = gql`
  query Agrupadores {
    agrupadores {
      valor
      nombre
      codigo
    }
  }
`;


export const TIPOLOGIAS = gql`
  query Tipologias($agrupador: Int!) {
    tipologias(agrupador: $agrupador) {
      id
      nombre
      abreviatura
      esDelSistema
      esPropia
    }
  }
`;
