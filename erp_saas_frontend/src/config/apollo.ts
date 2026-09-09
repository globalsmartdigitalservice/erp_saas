import { ApolloClient, InMemoryCache, createHttpLink, from } from "@apollo/client";
import { setContext } from "@apollo/client/link/context";

import { ENV } from "./environment";
import { idiomaGuardado } from "./preferencias-storage";
import { refreshLink } from "./refresh";

// `credentials` explícito: el login guarda el token en una cookie HttpOnly y
// sin esto el navegador no la manda. Hoy el proxy de Vite deja todo en el
// mismo origen y funcionaría igual, pero apuntar `VITE_API_URL` a otro host
// rompería la sesión sin dar ningún error.
const httpLink = createHttpLink({
  uri: ENV.API_URL,
  credentials: "include",
});


//  La EMPRESA ya no viaja acá: sale del claim `emp` del token, que está
// firmado. Como parámetro, cualquiera cambiaría el número y leería los datos
// de otro cliente.
//
//  El IDIOMA sí se queda, y no es una inconsistencia: no es una frontera de
// seguridad. Manipular esta cabecera solo cambia en qué idioma se ven los
// textos. Ver `MODULO_12_frontend.md` §4.2.
const contextoLink = setContext((_, { headers }) => {
  const idiomaId = idiomaGuardado();

  return {
    headers: {
      ...headers,
      ...(idiomaId ? { "X-Idioma": idiomaId } : {}),
    },
  };
});

export const client = new ApolloClient({
  //  El de renovación va PRIMERO: tiene que ver el error antes que nadie y
  // poder reenviar la operación por los que siguen.
  link: from([refreshLink, contextoLink, httpLink]),
  cache: new InMemoryCache(),
  defaultOptions: {

    watchQuery: { fetchPolicy: "network-only", errorPolicy: "all" },
    query: { fetchPolicy: "network-only", errorPolicy: "all" },
    mutate: { errorPolicy: "all" },
  },
});
