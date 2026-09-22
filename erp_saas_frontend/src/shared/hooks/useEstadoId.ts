import { useTipologias } from "@/shared/hooks/useTipologias";

/** El id del estado con esa abreviatura (`ABREV_ACTIVO`, `ABREV_BAJA`); null mientras carga o si no está. */
export function useEstadoId(abreviatura: string): { id: string | null; cargando: boolean } {
  const { opciones, cargando } = useTipologias("ESTADO_REGISTRO");

  return {
    id: opciones.find((opcion) => opcion.abreviatura === abreviatura)?.id ?? null,
    cargando,
  };
}
