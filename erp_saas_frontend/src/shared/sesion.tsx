import { useApolloClient, useMutation, useQuery } from "@apollo/client";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  type ReactNode,
} from "react";

import { SESION_EXPIRADA } from "@/config/refresh";
import { SALIR } from "@/modules/seguridad/graphql/seguridad.mutations";
import { SESION_ACTUAL } from "@/modules/seguridad/graphql/seguridad.queries";
import type {
  EmpresaDelUsuario,
  UsuarioDeLaSesion,
} from "@/modules/seguridad/types/sesion.types";

type EmpresaDeLaSesion = Pick<
  EmpresaDelUsuario,
  "empresaId" | "razonSocial" | "esMatriz"
>;

type Sesion = {
  usuario: UsuarioDeLaSesion | null;
  empresa: EmpresaDeLaSesion | null;
  permisos: string[];
  /** El arranque todavía no contestó: no se sabe si hay sesión o no. */
  cargando: boolean;
  /** Después de entrar, para que la app deje de creer que no hay nadie. */
  refrescar: () => Promise<void>;
  salir: () => Promise<void>;
};

type Respuesta = {
  yo: UsuarioDeLaSesion | null;
  miEmpresa: EmpresaDeLaSesion | null;
  misPermisos: string[];
};

const Contexto = createContext<Sesion | null>(null);

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
export function SesionProvider({ children }: { children: ReactNode }) {
  const client = useApolloClient();
  const { data, loading, refetch } = useQuery<Respuesta>(SESION_ACTUAL);
  const [pedirSalida] = useMutation(SALIR);

  const refrescar = useCallback(async () => {
    await refetch();
  }, [refetch]);

  const salir = useCallback(async () => {
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

    window.addEventListener(SESION_EXPIRADA, alExpirar);
    return () => window.removeEventListener(SESION_EXPIRADA, alExpirar);
  }, [refetch]);

  const valor = useMemo<Sesion>(
    () => ({
      usuario: data?.yo ?? null,
      empresa: data?.miEmpresa ?? null,
      permisos: data?.misPermisos ?? [],
      cargando: loading,
      refrescar,
      salir,
    }),
    [data, loading, refrescar, salir],
  );

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}

export function useSesion(): Sesion {
  const valor = useContext(Contexto);
  if (valor === null) {
    throw new Error(
      "useSesion() se usó fuera de <SesionProvider>. Revise App.tsx.",
    );
  }
  return valor;
}
