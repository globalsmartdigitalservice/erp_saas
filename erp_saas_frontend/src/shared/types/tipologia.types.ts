
export type Agrupador = {
  valor: number;
  nombre: string;
 
  codigo: string;
};

export type Tipologia = {
  id: string;
  nombre: string;
  abreviatura: string;
  esDelSistema: boolean;
  esPropia: boolean;
};


export type OrigenDeTipologia = "deFabrica" | "propia" | "heredada";

export function origenDe(fila: Tipologia): OrigenDeTipologia {
  if (fila.esDelSistema) return "deFabrica";
  return fila.esPropia ? "propia" : "heredada";
}

export const ABREV_ACTIVO = "A";
