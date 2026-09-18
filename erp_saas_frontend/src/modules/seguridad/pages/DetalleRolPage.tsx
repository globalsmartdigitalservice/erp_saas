import { useMutation, useQuery } from "@apollo/client";
import { AlertTriangle, ArrowLeft, Building2, Pencil, ShieldCheck, Trash2 } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";

import { DialogoRol } from "@/modules/seguridad/components/roles/DialogoRol";
import { PermisosDelRol } from "@/modules/seguridad/components/roles/PermisosDelRol";
import { DESACTIVAR_ROL } from "@/modules/seguridad/graphql/roles.mutations";
import { DETALLE_ROL } from "@/modules/seguridad/graphql/roles.queries";
import type { RolSinConteo } from "@/modules/seguridad/types/rol.types";
import { DialogoConfirmar } from "@/shared/components/DialogoConfirmar";
import { EstadoError } from "@/shared/components/EstadosTabla";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent } from "@/shared/components/ui/card";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { useTipologias } from "@/shared/hooks/useTipologias";
import { mensajeDeError } from "@/shared/lib/errores";
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
      <Button asChild variant="ghost" size="sm" className="-ml-2 gap-2">
        <Link to="..">
          <ArrowLeft size={16} aria-hidden="true" />
          {t("roles.volver")}
        </Link>
      </Button>

      {loading ? (
        <div className="space-y-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-72 w-full" />
        </div>
      ) : !rol ? (
        <EstadoError
          icono={AlertTriangle}
          titulo={t("roles.noExiste")}
          mensaje={mensajeDeError(error, t)}
          onReintentar={() => refetch()}
        />
      ) : (
        <div className="space-y-4 motion-safe:animate-in motion-safe:fade-in">
          <Cabecera rol={rol} />
          <PermisosDelRol rolId={rol.id} esHeredado={rol.esHeredado} />
        </div>
      )}
    </section>
  );
}

function Cabecera({ rol }: { rol: RolSinConteo }) {
  const { t } = useTranslation();
  const [dialogoAbierto, setDialogoAbierto] = useState(false);
  const estados = useTipologias("ESTADO_REGISTRO");

  const estado = estados.opciones.find((opcion) => opcion.id === rol.estadoId);
  const estaDeBaja = estado?.abreviatura === ABREV_BAJA;

  return (
    <Card>
      <CardContent className="flex flex-wrap items-start justify-between gap-4 pt-6">
        <div className="flex min-w-0 items-start gap-3">
          <span className="flex size-11 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
            <ShieldCheck className="size-5" aria-hidden="true" />
          </span>
          <div className="min-w-0 space-y-1">
            <h1 className="truncate font-heading text-xl font-semibold">{rol.nombre}</h1>
            <div className="flex flex-wrap items-center gap-2">
              {estado && <Badge variant="secondary">{estado.nombre}</Badge>}
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

            {!estaDeBaja && <DarDeBaja rol={rol} />}
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

  const [desactivar, { loading, error, reset }] = useMutation(DESACTIVAR_ROL, {
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
    <DialogoConfirmar
      destructivo
      titulo={t("roles.darDeBajaTitulo", { nombre: rol.nombre })}
      descripcion={t("roles.darDeBajaAyuda")}
      etiquetaConfirmar={t("roles.darDeBaja")}
      cargando={loading}
      error={mensajeDeError(error, t)}
      alCerrar={reset}
      onConfirmar={async () => {
        const resultado = await desactivar({ variables: { id: rol.id } });
        if (!resultado.data?.desactivarRol) return false;

        toast.success(t("roles.dadoDeBaja", { nombre: rol.nombre }));
        navegar("..");
      }}
    >
      <Button type="button" variant="outline" size="sm" className="gap-2">
        <Trash2 className="size-3.5" aria-hidden="true" />
        {t("roles.darDeBaja")}
      </Button>
    </DialogoConfirmar>
  );
}
