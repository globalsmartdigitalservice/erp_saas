import { useMutation, useQuery } from "@apollo/client";
import { Ban, Building2, Pencil, RotateCcw, ShieldCheck, ShieldOff } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router-dom";

import { DialogoRol } from "@/modules/seguridad/components/roles/DialogoRol";
import { PermisosDeRol } from "@/modules/seguridad/components/roles/PermisosDeRol";
import {
  DESACTIVAR_ROL,
  REACTIVAR_ROL,
} from "@/modules/seguridad/graphql/roles.mutations";
import { DETALLE_ROL } from "@/modules/seguridad/graphql/roles.queries";
import type { RolSinConteo } from "@/modules/seguridad/types/rol.types";
import { BackButton } from "@/shared/components/BackButton";
import { BadgeDeEstado } from "@/shared/components/BadgeDeEstado";
import { ConfirmDialog } from "@/shared/components/ConfirmDialog";
import { PageTitle } from "@/shared/components/PageTitle";
import { ErrorState, EmptyState } from "@/shared/components/TableStates";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent } from "@/shared/components/ui/card";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { useEstadoActivoId } from "@/shared/hooks/useEstadoActivoId";
import { useEstadoId } from "@/shared/hooks/useEstadoId";
import { useTipologias } from "@/shared/hooks/useTipologias";
import { ABREV_BAJA } from "@/shared/types/tipologia.types";

export function DetalleRolPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();

  const { data, loading, error, refetch } = useQuery<{ rol: RolSinConteo | null }>(DETALLE_ROL, {
    variables: { id },
    skip: !id,
  });

  const rol = data?.rol ?? null;

  return (
    <section className="space-y-4">
      <BackButton>{t("roles.volver")}</BackButton>

      {loading ? (
        <div className="space-y-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-72 w-full" />
        </div>
      ) : error && !rol ? (
        <ErrorState error={error} onRetry={() => refetch()} />
      ) : !rol ? (
        <EmptyState
          icon={ShieldOff}
          title={t("roles.noEsDeEstaEmpresa")}
          description={t("roles.noEsDeEstaEmpresaAyuda")}
        />
      ) : (
        <div className="space-y-4 motion-safe:animate-in motion-safe:fade-in">
          <Cabecera rol={rol} />
          <PermisosDeRol rolId={rol.id} esHeredado={rol.esHeredado} />
        </div>
      )}
    </section>
  );
}

function Cabecera({ rol }: { rol: RolSinConteo }) {
  const { t } = useTranslation();
  const [dialogoAbierto, setDialogoAbierto] = useState(false);
  const estados = useTipologias("ESTADO_REGISTRO");
  const activoId = useEstadoActivoId();
  const bajaId = useEstadoId(ABREV_BAJA).id;

  const nombreDeEstado = estados.opciones.find((opcion) => opcion.id === rol.estadoId)?.nombre;
  const estaDeBaja = rol.estadoId === bajaId;

  return (
    <Card>
      <CardContent className="flex flex-wrap items-start justify-between gap-4 pt-6">
        <div className="flex min-w-0 items-start gap-3">
          <span className="flex size-11 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
            <ShieldCheck className="size-5" aria-hidden="true" />
          </span>
          <div className="min-w-0 space-y-1">
            <PageTitle className="truncate">{rol.nombre}</PageTitle>
            <div className="flex flex-wrap items-center gap-2">
              {nombreDeEstado && (
                <BadgeDeEstado
                  estado={{ id: rol.estadoId, nombre: nombreDeEstado }}
                  activoId={activoId}
                />
              )}
              {rol.esHeredado && (
                <Badge variant="outline" className="gap-1 font-normal">
                  <Building2 className="size-3" aria-hidden="true" />
                  {t("roles.heredado")}
                </Badge>
              )}
            </div>
            {rol.esHeredado && (
              <p className="text-sm text-muted-foreground">{t("roles.heredadoAyuda")}</p>
            )}
          </div>
        </div>

        {!rol.esHeredado && (
          <div className="flex shrink-0 items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={() => setDialogoAbierto(true)}
            >
              <Pencil className="size-3.5" aria-hidden="true" />
              {t("roles.editar")}
            </Button>

            {estaDeBaja ? <Reactivar rol={rol} /> : <DarDeBaja rol={rol} />}
          </div>
        )}

        {dialogoAbierto && (
          <DialogoRol rol={rol} onCerrar={() => setDialogoAbierto(false)} />
        )}
      </CardContent>
    </Card>
  );
}

function DarDeBaja({ rol }: { rol: RolSinConteo }) {
  const { t } = useTranslation();
  const navegar = useNavigate();

  const [desactivar, mutacion] = useMutation(DESACTIVAR_ROL, {
    // Con un manejador puesto, la mutation devuelve el error en vez de
    // lanzarlo: el cartel del diálogo es el que lo muestra.
    onError: () => {},
    // La lista pide los roles filtrados por estado en el servidor, así que la
    // fila seguiría en "Activos" hasta volver a preguntar.
    update: (cache) => {
      cache.evict({ id: "ROOT_QUERY", fieldName: "roles" });
      cache.gc();
    },
  });

  return (
    <ConfirmDialog
      isDestructive
      title={t("roles.darDeBajaTitulo", { nombre: rol.nombre })}
      description={t("roles.darDeBajaAyuda")}
      confirmLabel={t("roles.darDeBaja")}
      mutation={mutacion}
      successMessage={t("roles.dadoDeBaja", { nombre: rol.nombre })}
      onConfirm={async () => {
        const resultado = await desactivar({ variables: { id: rol.id } });
        if (!resultado.data?.desactivarRol) return false;

        navegar("..");
      }}
    >
      <Button type="button" variant="outline" size="sm" className="gap-2">
        <Ban className="size-3.5" aria-hidden="true" />
        {t("roles.darDeBaja")}
      </Button>
    </ConfirmDialog>
  );
}

function Reactivar({ rol }: { rol: RolSinConteo }) {
  const { t } = useTranslation();

  const [reactivar, mutacion] = useMutation(REACTIVAR_ROL, {
    onError: () => {},
    update: (cache) => {
      cache.evict({ id: "ROOT_QUERY", fieldName: "roles" });
      cache.gc();
    },
  });

  return (
    <ConfirmDialog
      title={t("roles.reactivarTitulo", { nombre: rol.nombre })}
      description={t("roles.reactivarAyuda")}
      confirmLabel={t("roles.reactivar")}
      mutation={mutacion}
      successMessage={t("roles.reactivado", { nombre: rol.nombre })}
      onConfirm={async () => {
        const resultado = await reactivar({ variables: { id: rol.id } });
        if (!resultado.data?.reactivarRol) return false;
      }}
    >
      <Button type="button" variant="outline" size="sm" className="gap-2">
        <RotateCcw className="size-3.5" aria-hidden="true" />
        {t("roles.reactivar")}
      </Button>
    </ConfirmDialog>
  );
}
