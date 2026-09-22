import { useEstadoId } from "@/shared/hooks/useEstadoId";
import { ABREV_ACTIVO } from "@/shared/types/tipologia.types";

/** El id del estado Activo; null mientras carga o si no se encuentra. */
export function useEstadoActivoId(): string | null {
  return useEstadoId(ABREV_ACTIVO).id;
}
