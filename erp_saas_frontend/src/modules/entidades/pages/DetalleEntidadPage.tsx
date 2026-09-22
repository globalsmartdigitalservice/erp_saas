import { useMutation, useQuery } from "@apollo/client";
import { AlertTriangle, Ban, Pencil } from "lucide-react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { ContactosDeEntidad } from "@/modules/entidades/components/detalle/ContactosDeEntidad";
import { DatosGenerales } from "@/modules/entidades/components/detalle/DatosGenerales";
import { DireccionesDeEntidad } from "@/modules/entidades/components/detalle/DireccionesDeEntidad";
import { RolesDeEntidad } from "@/modules/entidades/components/detalle/RolesDeEntidad";
import { DESACTIVAR_ENTIDAD } from "@/modules/entidades/graphql/entidades.mutations";
import { ENTIDAD } from "@/modules/entidades/graphql/entidades.queries";
import {
  nombreCompleto,
  type Entidad,
} from "@/modules/entidades/types/entidad.types";
import { BackButton } from "@/shared/components/BackButton";
import { ConfirmDialog } from "@/shared/components/ConfirmDialog";
import { ErrorState, EmptyState } from "@/shared/components/TableStates";
import { Button } from "@/shared/components/ui/button";
import { Skeleton } from "@/shared/components/ui/skeleton";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/shared/components/ui/tabs";

const PESTANAS = ["roles", "direcciones", "contactos"] as const;
type Pestana = (typeof PESTANAS)[number];

function esPestana(valor: string | null): valor is Pestana {
  return PESTANAS.some((pestana) => pestana === valor);
}

export function DetalleEntidadPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();

  const [parametros, setParametros] = useSearchParams();
  const elegida = parametros.get("pestana");
  const pestana: Pestana = esPestana(elegida) ? elegida : "roles";

  const { data, loading, error, refetch } = useQuery<{
    entidad: Entidad | null;
  }>(ENTIDAD, {
    variables: { id },
    skip: !id,
  });

  const entidad = data?.entidad ?? null;

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <BackButton>{t("entidades.volver")}</BackButton>

        {entidad && (
          <div className="flex items-center gap-2">
            <BajaDeEntidad entidad={entidad} />

            <Button asChild variant="outline" size="sm" className="gap-2">
              <Link to="editar">
                <Pencil aria-hidden="true" />
                {t("entidades.editar")}
              </Link>
            </Button>
          </div>
        )}
      </div>

      {loading ? (
        <div className="space-y-3">
          <Skeleton className="h-28 w-full" />
          <Skeleton className="h-40 w-full" />
        </div>
      ) : error && entidad === null ? (
        <ErrorState error={error} onRetry={() => refetch()} />
      ) : entidad === null ? (
        <EmptyState
          icon={AlertTriangle}
          title={t("entidades.noExiste")}
          description={t("entidades.noExisteAyuda")}
        />
      ) : (
        <div className="space-y-4">
          <DatosGenerales entidad={entidad} />

          <Tabs
            value={pestana}
            onValueChange={(valor) =>
              setParametros({ pestana: valor }, { replace: true })
            }
            className="space-y-4"
          >
            <TabsList>
              <Pestania
                valor="roles"
                etiqueta={t("entidades.roles")}
                cuantos={entidad.roles?.length ?? 0}
              />
              <Pestania
                valor="direcciones"
                etiqueta={t("entidades.direcciones")}
                cuantos={entidad.direcciones?.length ?? 0}
              />
              <Pestania
                valor="contactos"
                etiqueta={t("entidades.contactos")}
                cuantos={entidad.contactos?.length ?? 0}
              />
            </TabsList>

            <TabsContent value="roles">
              <RolesDeEntidad
                entidadId={entidad.id}
                roles={entidad.roles ?? []}
              />
            </TabsContent>

            <TabsContent value="direcciones">
              <DireccionesDeEntidad
                entidadId={entidad.id}
                direcciones={entidad.direcciones ?? []}
              />
            </TabsContent>

            <TabsContent value="contactos">
              <ContactosDeEntidad
                entidadId={entidad.id}
                contactos={entidad.contactos ?? []}
              />
            </TabsContent>
          </Tabs>
        </div>
      )}
    </section>
  );
}

function Pestania({
  valor,
  etiqueta,
  cuantos,
}: {
  valor: Pestana;
  etiqueta: string;
  cuantos: number;
}) {
  return (
    <TabsTrigger value={valor} className="gap-2">
      {etiqueta}
      <span className="rounded-full bg-muted px-1.5 text-xs tabular-nums text-muted-foreground">
        {cuantos}
      </span>
    </TabsTrigger>
  );
}

function BajaDeEntidad({ entidad }: { entidad: Entidad }) {
  const { t } = useTranslation();

  const [desactivar, mutacion] = useMutation(
    DESACTIVAR_ENTIDAD,
    { refetchQueries: [ENTIDAD] },
  );

  return (
    <ConfirmDialog
      title={t("entidades.bajaEntidadTitulo", {
        nombre: nombreCompleto(entidad),
      })}
      description={t("entidades.bajaEntidadAyuda")}
      confirmLabel={t("entidades.darDeBaja")}
      mutation={mutacion}
      successMessage={t("entidades.entidadDadaDeBaja")}
      onConfirm={async () => {
        const resultado = await desactivar({ variables: { id: entidad.id } });

        if (!resultado.data?.desactivarEntidad) return false;
      }}
    >
      <Button
        variant="ghost"
        size="sm"
        className="gap-2 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
      >
        <Ban aria-hidden="true" />
        {t("entidades.darDeBaja")}
      </Button>
    </ConfirmDialog>
  );
}
