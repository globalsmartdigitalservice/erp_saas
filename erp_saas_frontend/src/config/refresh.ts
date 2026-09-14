import { Observable, fromPromise, type FetchResult } from "@apollo/client";
import { onError } from "@apollo/client/link/error";

import { ENV } from "./environment";

/** El aviso de que ya no hay sesión. Lo escucha el proveedor de sesión.
 *
 * Lleva `_EVENT` porque el código de error del backend se llama igual y vive
 * en este mismo archivo: son dos cosas distintas, y una sola palabra para las
 * dos no compila. */
export const SESSION_EXPIRED_EVENT = "erp:session-expired";

// Los códigos viajan en `extensions.code`, la convención de Apollo. Se decide
// por código y NO por el texto del mensaje: reescribir una palabra en el
// backend dejaría de renovar sin dar ningún error.
const UNAUTHENTICATED = "UNAUTHENTICATED";
const SESSION_EXPIRED = "SESSION_EXPIRED";

//  Ventana para los pedidos que salieron ANTES de que terminara la renovación
// anterior y recién ahora vuelven con el error. Ya viajan con el token nuevo,
// así que alcanza con reintentarlos. Sin esta ventana arrancan otra
// renovación, y si son dos, el refresh rota una vez y el segundo se queda con
// el viejo: la sesión muere sin motivo.
const REFRESH_COOLDOWN_MS = 2000;

const REFRESH_MUTATION = "mutation { refreshSession { usuario { id } } }";

let refreshPromise: Promise<boolean> | null = null;
let lastRefreshSuccessAt = 0;

async function fetchRefresh(): Promise<boolean> {
  //  Va por `fetch` y no por el cliente de Apollo a propósito: si pasara por
  // el mismo cliente, una renovación que falla volvería a entrar en este
  // link y se mordería la cola.
  const respuesta = await fetch(ENV.API_URL, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: REFRESH_MUTATION }),
  });

  if (!respuesta.ok) return false;

  // GraphQL responde 200 aunque falle: el veredicto está en `errors`.
  const cuerpo: { errors?: unknown[] } = await respuesta.json();
  return !cuerpo.errors?.length;
}

/**
 * Single-flight: una sola renovación en vuelo, las demás esperan su resultado.
 *
 *  El refresh ROTA en cada uso — el backend guarda cuál es el único válido y
 * mata el anterior. Cuatro consultas que fallan juntas dispararían cuatro
 * renovaciones con el mismo refresh, ganaría una y las otras tres verían
 * "la sesión venció" con la sesión intacta.
 */
function refreshOnce(): Promise<boolean> {
  refreshPromise ??= fetchRefresh()
    .catch(() => false)
    .then((ok) => {
      if (ok) lastRefreshSuccessAt = Date.now();
      return ok;
    })
    .finally(() => {
      //  Obligatorio: sin esto la primera renovación queda cacheada para
      // siempre y la próxima vez que venza el token nadie renueva.
      refreshPromise = null;
    });

  return refreshPromise;
}

function sinSesion(): Observable<FetchResult> {
  window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
  return new Observable<FetchResult>((observador) => observador.complete());
}

export const refreshLink = onError(({ graphQLErrors, operation, forward }) => {
  if (!graphQLErrors?.length) return;

  const codes = graphQLErrors.map((error) => error.extensions?.code);

  // El refresh ya no sirve y el backend borró las cookies: renovar de nuevo
  // no puede salir bien.
  if (codes.includes(SESSION_EXPIRED)) return sinSesion();

  if (!codes.includes(UNAUTHENTICATED)) return;

  //  Un reintento por operación. Sin este candado, un error que no se arregla
  // renovando daría vueltas para siempre.
  if (operation.getContext().refreshAttempted) return sinSesion();
  operation.setContext({ refreshAttempted: true });

  const desdeLaUltima = Date.now() - lastRefreshSuccessAt;
  if (!refreshPromise && desdeLaUltima < REFRESH_COOLDOWN_MS) {
    return forward(operation);
  }

  return fromPromise(refreshOnce()).flatMap((ok) =>
    ok ? forward(operation) : sinSesion(),
  );
});
