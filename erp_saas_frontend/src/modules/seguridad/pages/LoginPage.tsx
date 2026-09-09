import { useMutation } from "@apollo/client";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Navigate, useLocation } from "react-router-dom";

import { EmpresasDelUsuario } from "@/modules/seguridad/components/EmpresasDelUsuario";
import { FormularioLogin } from "@/modules/seguridad/components/FormularioLogin";
import {
  ELEGIR_EMPRESA,
  INGRESAR,
} from "@/modules/seguridad/graphql/seguridad.mutations";
import type {
  Credenciales,
  EmpresaDelUsuario,
  ResultadoIngreso,
} from "@/modules/seguridad/types/sesion.types";
import { mensajeDeError } from "@/shared/lib/errores";
import { useSesion } from "@/shared/sesion";


export function LoginPage() {
  const { t } = useTranslation();
  const ubicacion = useLocation();
  const { usuario, cargando, refrescar } = useSesion();

 
  const destino = (ubicacion.state as { desde?: string } | null)?.desde ?? "/";

  const [credenciales, setCredenciales] = useState<Credenciales | null>(null);
  const [empresas, setEmpresas] = useState<EmpresaDelUsuario[]>([]);
  const [eligiendo, setEligiendo] = useState<string | null>(null);
  const [entrando, setEntrando] = useState(false);

  const [ingresar, ingreso] = useMutation<{ ingresar: ResultadoIngreso }>(INGRESAR);

  
  const [elegirEmpresa, eleccion] = useMutation<{
    elegirEmpresa: Pick<ResultadoIngreso, "necesitaElegirEmpresa" | "usuario">;
  }>(ELEGIR_EMPRESA);

  const enSegundoPaso = empresas.length > 0;

 
  if (!cargando && usuario !== null) {
    return <Navigate to={destino} replace />;
  }

  async function entrar(datos: Credenciales) {
    setEntrando(true);
    const resultado = await ingresar({ variables: { datos } });
    const respuesta = resultado.data?.ingresar;

    if (!respuesta) {
      setEntrando(false);
      return;
    }

    if (respuesta.necesitaElegirEmpresa) {
      setCredenciales(datos);
      setEmpresas(respuesta.empresas);
      setEntrando(false);
      return;
    }

    await refrescar();
  }

  async function abrirEn(empresaId: string) {
    if (!credenciales) return;

    setEligiendo(empresaId);
    const resultado = await elegirEmpresa({
      variables: { datos: credenciales, empresaId },
    });

    if (!resultado.data?.elegirEmpresa) {
      setEligiendo(null);
      return;
    }

    setCredenciales(null);
    await refrescar();
  }

  function volverAlPrimerPaso() {
    setCredenciales(null);
    setEmpresas([]);
  }

  return (
    <main className="grid min-h-screen lg:grid-cols-[1fr_1.15fr]">
      <aside className="relative hidden overflow-hidden bg-sidebar p-12 text-sidebar-foreground lg:flex lg:flex-col lg:justify-between">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -right-24 -top-24 size-96 rounded-full opacity-20 blur-3xl"
          style={{ background: "var(--primary)" }}
        />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -bottom-32 -left-16 size-80 rounded-full opacity-10 blur-3xl"
          style={{ background: "var(--primary)" }}
        />

        <p className="font-heading text-2xl font-semibold tracking-tight">ERP</p>

        <div className="relative max-w-sm space-y-3">
          <p className="font-heading text-3xl font-semibold leading-tight">
            {t("login.panelTitulo")}
          </p>
          <p className="text-sm leading-relaxed text-sidebar-foreground/70">
            {t("login.panelTexto")}
          </p>
        </div>

        <div
          aria-hidden="true"
          className="h-1 w-16 rounded-full"
          style={{ background: "var(--primary)" }}
        />
      </aside>

      <div className="flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm space-y-8">
          <header className="space-y-2">
            <p className="font-heading text-xl font-semibold tracking-tight lg:hidden">
              ERP
            </p>
            <h1 className="font-heading text-2xl font-semibold tracking-tight">
              {enSegundoPaso ? t("login.tituloEmpresa") : t("login.titulo")}
            </h1>
            <p className="text-sm text-muted-foreground">
              {enSegundoPaso ? t("login.ayudaEmpresa") : t("login.ayuda")}
            </p>
          </header>

          {enSegundoPaso ? (
            <div
              key="empresas"
              className="motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-right-2"
            >
              <EmpresasDelUsuario
                empresas={empresas}
                eligiendo={eligiendo}
                error={mensajeDeError(eleccion.error, t)}
                onElegir={abrirEn}
                onVolver={volverAlPrimerPaso}
              />
            </div>
          ) : (
            <FormularioLogin
              enviando={ingreso.loading || entrando}
              error={mensajeDeError(ingreso.error, t)}
              onEnviar={entrar}
            />
          )}
        </div>
      </div>
    </main>
  );
}
