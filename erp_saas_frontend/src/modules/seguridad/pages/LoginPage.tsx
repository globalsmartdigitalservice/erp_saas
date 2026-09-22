import { useMutation } from "@apollo/client";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Navigate, useLocation } from "react-router-dom";

import { AccesoLayout } from "@/modules/seguridad/components/AccesoLayout";
import { EmpresasDeUsuario } from "@/modules/seguridad/components/EmpresasDeUsuario";
import { FormularioLogin } from "@/modules/seguridad/components/FormularioLogin";
import {
  ELEGIR_EMPRESA,
  LOGIN,
} from "@/modules/seguridad/graphql/seguridad.mutations";
import type {
  Credenciales,
  EmpresaDeUsuario,
  ResultadoLogin,
} from "@/modules/seguridad/types/sesion.types";
import { mensajeDeError } from "@/shared/lib/errores";
import { useSession } from "@/shared/session";


export function LoginPage() {
  const { t } = useTranslation();
  const ubicacion = useLocation();
  const { usuario, cargando, refrescar } = useSession();

  const destino = (ubicacion.state as { desde?: string } | null)?.desde ?? "/";

  const [credenciales, setCredenciales] = useState<Credenciales | null>(null);
  const [empresas, setEmpresas] = useState<EmpresaDeUsuario[]>([]);
  const [eligiendo, setEligiendo] = useState<string | null>(null);
  const [entrando, setEntrando] = useState(false);

  const [login, ingreso] = useMutation<{ login: ResultadoLogin }>(LOGIN);

  const [elegirEmpresa, eleccion] = useMutation<{
    elegirEmpresa: Pick<ResultadoLogin, "necesitaElegirEmpresa" | "usuario">;
  }>(ELEGIR_EMPRESA);

  const enSegundoPaso = empresas.length > 0;

  if (!cargando && usuario !== null) {
    return <Navigate to={destino} replace />;
  }

  async function entrar(datos: Credenciales) {
    setEntrando(true);
    // Sin backend, el await lanza en vez de devolver: el finally es lo que
    // evita que el botón quede trabado.
    try {
      const resultado = await login({ variables: { datos } });
      const respuesta = resultado.data?.login;
      if (!respuesta) return;

      if (respuesta.necesitaElegirEmpresa) {
        setCredenciales(datos);
        setEmpresas(respuesta.empresas);
        return;
      }

      await refrescar();
    } finally {
      setEntrando(false);
    }
  }

  async function abrirEn(empresaId: string) {
    if (!credenciales) return;

    setEligiendo(empresaId);
    try {
      const resultado = await elegirEmpresa({
        variables: { datos: credenciales, empresaId },
      });
      if (!resultado.data?.elegirEmpresa) return;

      setCredenciales(null);
      await refrescar();
    } finally {
      setEligiendo(null);
    }
  }

  function volverAlPrimerPaso() {
    setEmpresas([]);
  }

  return (
    <AccesoLayout
      titulo={enSegundoPaso ? t("login.tituloEmpresa") : t("login.titulo")}
      ayuda={enSegundoPaso ? t("login.ayudaEmpresa") : t("login.ayuda")}
    >
      {enSegundoPaso ? (
        <div
          key="empresas"
          className="motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-right-2"
        >
          <EmpresasDeUsuario
            empresas={empresas}
            eligiendo={eligiendo}
            error={mensajeDeError(eleccion.error, t)}
            onElegir={abrirEn}
            onVolver={volverAlPrimerPaso}
          />
        </div>
      ) : (
        <FormularioLogin
          inicial={credenciales}
          enviando={ingreso.loading || entrando}
          error={mensajeDeError(ingreso.error, t)}
          onEnviar={entrar}
          onEditar={ingreso.reset}
        />
      )}
    </AccesoLayout>
  );
}
