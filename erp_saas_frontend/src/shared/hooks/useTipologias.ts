import { useQuery } from "@apollo/client";

import { ENV } from "@/config/environment";
import {
  AGRUPADORES,
  TIPOLOGIAS,
} from "@/shared/graphql/tipologias.queries";
import type { Agrupador, Tipologia } from "@/shared/types/tipologia.types";


type Resultado = {
  opciones: Tipologia[];
  cargando: boolean;

  existe: boolean;
};

export function useTipologias(codigo: string): Resultado {
  const listas = useQuery<{ agrupadores: Agrupador[] }>(AGRUPADORES);

  const agrupador =
    listas.data?.agrupadores.find((a) => a.codigo === codigo)?.valor ?? null;

  const valores = useQuery<{ tipologias: Tipologia[] }>(TIPOLOGIAS, {
    variables: { agrupador },
    skip: agrupador === null,
  });


  if (ENV.IS_DEV && !listas.loading && listas.data && agrupador === null) {
    console.warn(
      `[useTipologias] No existe ningún agrupador con código "${codigo}". ` +
        `El combo va a quedar vacío. Códigos disponibles: ` +
        `${listas.data.agrupadores.map((a) => a.codigo).join(", ") || "(ninguno: falta correr cargar_semillas)"}`,
    );
  }

  return {
    opciones: valores.data?.tipologias ?? [],
    cargando: listas.loading || valores.loading,
    existe: agrupador !== null,
  };
}
