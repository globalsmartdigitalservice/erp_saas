import { useApolloClient, useMutation, useQuery } from "@apollo/client";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  type ReactNode,
} from "react";

import { SESSION_EXPIRED_EVENT } from "@/config/refresh";
import { LOGOUT } from "@/modules/seguridad/graphql/seguridad.mutations";
import { SESION_ACTUAL } from "@/modules/seguridad/graphql/seguridad.queries";
import type {
  EmpresaDelUsuario,
  UsuarioDeLaSesion,
} from "@/modules/seguridad/types/sesion.types";

type EmpresaDeLaSesion = Pick<
  EmpresaDelUsuario,
  "empresaId" | "razonSocial" | "esMatriz"
>;

type Session = {
  usuario: UsuarioDeLaSesion | null;
  empresa: EmpresaDeLaSesion | null;
  permisos: string[];
  /** El arranque todavía no contestó: no se sabe si hay sesión o no. */
  cargando: boolean;
  /** Después de entrar, para que la app deje de creer que no hay nadie. */
  refrescar: () => Promise<void>;
  logout: () => Promise<void>;
};

type Respuesta = {
  me: UsuarioDeLaSesion | null;
  miEmpresa: EmpresaDeLaSesion | null;
  misPermisos: string[];
};

const Contexto = createContext<Session | null>(null);

/**
 * Quién está conectado, según el backend.
 *
 *  NO GUARDA NADA EN EL NAVEGADOR, a diferencia de `preferencias.tsx`. La
 * sesión vive en una cookie `HttpOnly` que el frontend no puede leer, así que
 * la única fuente de verdad es preguntarle al backend. Copiarla al
 * `localStorage` daría una app que se cree logueada con la sesión ya cerrada.
 *
 *  ESTE PROVIDER NO NAVEGA. Solo dice qué hay; quien manda al login es
 * `<ProtectedRoute>`. Así la regla de a dónde ir vive en un lugar y no en dos.
 */
export function SessionProvider({ children }: { children: ReactNode }) {
  const client = useApolloClient();
  const { data, loading, refetch } = useQuery<Respuesta>(SESION_ACTUAL);
  const [pedirSalida] = useMutation(LOGOUT);

  const refrescar = useCallback(async () => {
    await refetch();
  }, [refetch]);

  const logout = useCallback(async () => {
    await pedirSalida();
    // `resetStore` vuelve a correr las consultas activas, y la del arranque
    // es una de ellas: la sesión queda en null sin pedirla a mano.
    await client.resetStore();
  }, [client, pedirSalida]);

  useEffect(() => {
    //  El link de renovación avisa cuando ya no hay nada que renovar. Se
    // vuelve a preguntar en vez de asumir: si el aviso llegó tarde y la
    // sesión revivió, no se echa a nadie por las dudas.
    function alExpirar() {
      void refetch();
    }

    window.addEventListener(SESSION_EXPIRED_EVENT, alExpirar);
    return () => window.removeEventListener(SESSION_EXPIRED_EVENT, alExpirar);
  }, [refetch]);

  const valor = useMemo<Session>(
    () => ({
      usuario: data?.me ?? null,
      empresa: data?.miEmpresa ?? null,
      permisos: data?.misPermisos ?? [],
      cargando: loading,
      refrescar,
      logout,
    }),
    [data, loading, refrescar, logout],
  );

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}

export function useSession(): Session {
  const valor = useContext(Contexto);
  if (valor === null) {
    throw new Error(
      "useSession() se usó fuera de <SessionProvider>. Revise App.tsx.",
    );
  }
  return valor;
}
