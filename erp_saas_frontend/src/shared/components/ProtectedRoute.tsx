import { Loader2 } from "lucide-react";
import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useSession } from "@/shared/session";

/**
 * Deja pasar solo con sesión abierta.
 *
 *  MIENTRAS LA CONSULTA DEL ARRANQUE ESTÁ EN VUELO NO SE DECIDE NADA. Sin esta
 * espera, cada recarga de página manda al login por un instante —todavía no
 * llegó la respuesta, así que `usuario` es null— y recién después vuelve. Se
 * ve como un parpadeo y hace dudar de que la sesión funcione.
 *
 *  Esconder una ruta NO es seguridad: quien pida los datos igual choca con las
 * guardas del backend. Esto es comodidad, para no mostrar una pantalla que va
 * a venir vacía.
 */
export function ProtectedRoute() {
  const { usuario, cargando } = useSession();
  const ubicacion = useLocation();

  if (cargando) {
    return (
      <div
        role="status"
        className="flex min-h-screen items-center justify-center text-muted-foreground"
      >
        <Loader2 className="size-6 animate-spin" aria-hidden="true" />
      </div>
    );
  }

  if (usuario === null) {

    return <Navigate to="/login" replace state={{ desde: ubicacion.pathname }} />;
  }

  return <Outlet />;
}
