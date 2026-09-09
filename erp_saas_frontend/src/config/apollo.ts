import { ApolloClient, InMemoryCache, createHttpLink, from } from "@apollo/client";
import { setContext } from "@apollo/client/link/context";

import { ENV } from "./environment";
import { empresaGuardada, idiomaGuardado } from "./preferencias-storage";

const httpLink = createHttpLink({ uri: ENV.API_URL });


const contextoLink = setContext((_, { headers }) => {
  const empresaId = empresaGuardada();
  const idiomaId = idiomaGuardado();

  return {
    headers: {
      ...headers,

      ...(empresaId ? { "X-Empresa-Id": empresaId } : {}),
      ...(idiomaId ? { "X-Idioma": idiomaId } : {}),
    },
  };
});

export const client = new ApolloClient({
  link: from([contextoLink, httpLink]),
  cache: new InMemoryCache(),
  defaultOptions: {

    watchQuery: { fetchPolicy: "network-only", errorPolicy: "all" },
    query: { fetchPolicy: "network-only", errorPolicy: "all" },
    mutate: { errorPolicy: "all" },
  },
});
