import { useLazyQuery, useMutation } from "@apollo/client";
import { Info, Loader2, Mail, UserCheck } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { BusquedaPorCorreo } from "@/modules/seguridad/components/miembros/BusquedaPorCorreo";
import { DialogoPasswordTemporal } from "@/modules/seguridad/components/miembros/DialogoPasswordTemporal";
import { FormularioPersonaNueva } from "@/modules/seguridad/components/miembros/FormularioPersonaNueva";
import { SeleccionDeRoles } from "@/modules/seguridad/components/miembros/SeleccionDeRoles";
import { DAR_DE_ALTA_MIEMBRO } from "@/modules/seguridad/graphql/miembros.mutations";
import {
  MIEMBROS,
  PERSONA_POR_CORREO,
} from "@/modules/seguridad/graphql/miembros.queries";
import type {
  AltaDeMiembro,
  DatosDePersonaNueva,
  PersonaEncontrada,
} from "@/modules/seguridad/types/miembro.types";
import { BackButton } from "@/shared/components/BackButton";
import { ErrorAlert } from "@/shared/components/ErrorAlert";
import { PageTitle } from "@/shared/components/PageTitle";
import { Alert, AlertDescription, AlertTitle } from "@/shared/components/ui/alert";
import { Button } from "@/shared/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from "@/shared/components/ui/card";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { mensajeDeError } from "@/shared/lib/errores";
import { useSession } from "@/shared/session";

type PedidoDeAlta =
  | { usuarioId: string; rolIds: string[] }
  | { persona: DatosDePersonaNueva; rolIds: string[] };

type Temporal = { nombre: string; password: string };

export function AltaMiembroPage() {
  const { t } = useTranslation();
  const navegar = useNavigate();
  const { empresa } = useSession();

  const [correo, setCorreo] = useState<string | null>(null);
  const [rolIds, setRolIds] = useState<string[]>([]);
  const [temporal, setTemporal] = useState<Temporal | null>(null);

  const [buscar, busqueda] = useLazyQuery<{
    personaPorCorreo: PersonaEncontrada | null;
  }>(PERSONA_POR_CORREO, { fetchPolicy: "network-only" });

  const [darDeAlta, alta] = useMutation<{ darDeAltaMiembro: AltaDeMiembro }>(
    DAR_DE_ALTA_MIEMBRO,
    { refetchQueries: [MIEMBROS] },
  );

  const resultado = busqueda.data ? busqueda.data.personaPorCorreo : undefined;
  const hayResultado = correo !== null && !busqueda.loading && !busqueda.error;

  async function alBuscar(email: string) {
    setCorreo(email);
    setRolIds([]);
    alta.reset();
    await buscar({ variables: { email } });
  }

  function buscarOtroCorreo() {
    setCorreo(null);
    alta.reset();
  }

  async function registrar(datos: PedidoDeAlta) {
    const respuesta = await darDeAlta({ variables: { datos } });
    const hecho = respuesta.data?.darDeAltaMiembro;
    if (!hecho) return;

    toast.success(t("miembros.creado"));

    if (hecho.passwordTemporal) {
      const persona = hecho.membresia.usuario;
      setTemporal({
        nombre: persona?.nombreCompleto || persona?.username || "",
        password: hecho.passwordTemporal,
      });
      return;
    }

    navegar("..");
  }

  return (
    <section className="mx-auto max-w-3xl space-y-4">
      <BackButton>{t("miembros.volver")}</BackButton>

      <Card>
        <CardHeader>
          <PageTitle>{t("miembros.nuevo")}</PageTitle>
          <CardDescription>{t("miembros.altaAyuda")}</CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          {correo === null ? (
            <BusquedaPorCorreo buscando={busqueda.loading} onBuscar={alBuscar} />
          ) : (
            <div className="flex flex-wrap items-center justify-between gap-2 rounded-md bg-muted/40 px-3 py-2 text-sm">
              <span className="flex min-w-0 items-center gap-2">
                <Mail size={14} className="shrink-0 text-muted-foreground" aria-hidden="true" />
                <span className="truncate">{correo}</span>
              </span>
              <Button variant="ghost" size="sm" onClick={buscarOtroCorreo} disabled={alta.loading}>
                {t("miembros.otroCorreo")}
              </Button>
            </div>
          )}

          {correo !== null && busqueda.loading && <Skeleton className="h-28 w-full" />}

          {correo !== null && <ErrorAlert message={mensajeDeError(busqueda.error, t)} />}

          {hayResultado && resultado?.trabajaAca && (
            <Alert className="motion-safe:animate-in motion-safe:fade-in">
              <Info aria-hidden="true" />
              <AlertTitle>{t("miembros.yaTrabajaAca", { nombre: resultado.nombreCompleto })}</AlertTitle>
              <AlertDescription>{t("miembros.yaTrabajaAcaAyuda")}</AlertDescription>
            </Alert>
          )}

          {hayResultado && resultado && !resultado.trabajaAca && (
            <div className="space-y-5 motion-safe:animate-in motion-safe:fade-in">
              <div className="flex items-center gap-3 rounded-lg border bg-primary/5 p-4">
                <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <UserCheck size={18} aria-hidden="true" />
                </span>
                <div className="min-w-0">
                  <p className="truncate font-medium">{resultado.nombreCompleto}</p>
                  <p className="text-sm text-muted-foreground">
                    {t("miembros.existeEnOrganizacionAyuda")}
                  </p>
                </div>
              </div>

              <SeleccionDeRoles seleccionados={rolIds} onCambiar={setRolIds} />

              <ErrorAlert message={mensajeDeError(alta.error, t)} />

              <div className="flex justify-end">
                <Button
                  className="gap-2"
                  onClick={() => registrar({ usuarioId: resultado.usuarioId, rolIds })}
                  disabled={alta.loading}
                  aria-busy={alta.loading || undefined}
                >
                  {alta.loading && <Loader2 className="animate-spin" aria-hidden="true" />}
                  {alta.loading
                    ? t("miembros.agregando")
                    : t("miembros.agregar", { empresa: empresa?.razonSocial ?? "" })}
                </Button>
              </div>
            </div>
          )}

          {hayResultado && resultado === null && (
            <div className="space-y-5 motion-safe:animate-in motion-safe:fade-in">
              <div>
                <p className="font-medium">{t("miembros.noExiste")}</p>
                <p className="text-sm text-muted-foreground">{t("miembros.noExisteAyuda")}</p>
              </div>

              <FormularioPersonaNueva
                key={correo}
                email={correo}
                guardando={alta.loading}
                error={mensajeDeError(alta.error, t)}
                onGuardar={(persona, roles) => registrar({ persona, rolIds: roles })}
              />
            </div>
          )}
        </CardContent>
      </Card>

      {temporal && (
        <DialogoPasswordTemporal
          nombre={temporal.nombre}
          password={temporal.password}
          onCerrar={() => navegar("..")}
        />
      )}
    </section>
  );
}
