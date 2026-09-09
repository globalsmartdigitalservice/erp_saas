import { useApolloClient } from "@apollo/client";
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useTranslation } from "react-i18next";

import { IDIOMA_POR_DEFECTO } from "@/config/i18n";
import {
  empresaGuardada,
  guardarEmpresa,
  guardarIdioma,
  idiomaCodigoGuardado,
  idiomaGuardado,
} from "@/config/preferencias-storage";



type Preferencias = {
  empresaId: string | null;
  idiomaId: string | null;
  idiomaCodigo: string;
  elegirEmpresa: (empresaId: string) => void;
  elegirIdioma: (idiomaId: string, codigo: string) => void;
};

const Contexto = createContext<Preferencias | null>(null);

export function PreferenciasProvider({ children }: { children: ReactNode }) {

  const client = useApolloClient();
  const { i18n } = useTranslation();

  const [empresaId, setEmpresaId] = useState<string | null>(empresaGuardada);
  const [idiomaId, setIdiomaId] = useState<string | null>(idiomaGuardado);
  const [idiomaCodigo, setIdiomaCodigo] = useState<string>(
    () => idiomaCodigoGuardado() || IDIOMA_POR_DEFECTO,
  );

  const elegirEmpresa = useCallback(
    (nuevo: string) => {
      guardarEmpresa(nuevo);
      setEmpresaId(nuevo);

      void client.resetStore();
    },
    [client],
  );

  const elegirIdioma = useCallback(
    (nuevo: string, codigo: string) => {
      guardarIdioma(nuevo, codigo);
      setIdiomaId(nuevo);
      setIdiomaCodigo(codigo);


      void i18n.changeLanguage(codigo);
      void client.resetStore();
    },
    [client, i18n],
  );

  const valor = useMemo(
    () => ({ empresaId, idiomaId, idiomaCodigo, elegirEmpresa, elegirIdioma }),
    [empresaId, idiomaId, idiomaCodigo, elegirEmpresa, elegirIdioma],
  );

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}

export function usePreferencias(): Preferencias {
  const valor = useContext(Contexto);
  if (valor === null) {
    throw new Error(
      "usePreferencias() se usó fuera de <PreferenciasProvider>. " +
        "Revisá App.tsx.",
    );
  }
  return valor;
}
