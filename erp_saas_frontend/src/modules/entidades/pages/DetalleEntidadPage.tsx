import { useMutation, useQuery } from "@apollo/client";
import { AlertTriangle, ArrowLeft, Ban, Pencil } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

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
import { DialogoConfirmar } from "@/shared/components/DialogoConfirmar";
import { EstadoError, EstadoVacio } from "@/shared/components/EstadosTabla";
import { Button } from "@/shared/components/ui/button";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { mensajeDeError } from "@/shared/lib/errores";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/shared/components/ui/tabs";


export function DetalleEntidadPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();

  const { data, loading, error, refetch } = useQuery<{
    entidad: Entidad | null;
  }>(ENTIDAD, {
    variables: { id },
    skip: !id,
  });

  const entidad = data?.entidad ?? null;

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <Button asChild variant="ghost" size="sm" className="-ml-2 gap-2">
          <Link to="..">
            <ArrowLeft size={16} />
            {t("entidades.volver")}
          </Link>
        </Button>

        {entidad && (
          <div className="flex items-center gap-2">
            <BajaDeEntidad entidad={entidad} />

            <Button asChild variant="outline" size="sm" className="gap-2">
              <Link to="editar">
                <Pencil size={14} />
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
      ) : error ? (
        <EstadoError icono={AlertTriangle} onReintentar={() => refetch()} />
      ) : entidad === null ? (
        <EstadoVacio
          icono={AlertTriangle}
          titulo={t("entidades.noExiste")}
          descripcion={t("entidades.noExisteAyuda")}
        />
      ) : (
        <div className="space-y-4">
          <DatosGenerales entidad={entidad} />


          <Tabs defaultValue="roles" className="space-y-4">
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
  valor: string;
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

  const [desactivar, { loading, error, reset }] = useMutation(
    DESACTIVAR_ENTIDAD,
    { refetchQueries: [ENTIDAD] },
  );

  return (
    <DialogoConfirmar
      titulo={t("entidades.bajaEntidadTitulo", {
        nombre: nombreCompleto(entidad),
      })}
      descripcion={t("entidades.bajaEntidadAyuda")}
      etiquetaConfirmar={t("entidades.darDeBaja")}
      cargando={loading}
      error={mensajeDeError(error, t)}
      alCerrar={reset}
      onConfirmar={async () => {
        const resultado = await desactivar({ variables: { id: entidad.id } });

        if (!resultado.data?.desactivarEntidad) return false;

        toast.success(t("entidades.entidadDadaDeBaja"));
      }}
    >
      <Button
        variant="ghost"
        size="sm"
        className="gap-2 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
      >
        <Ban size={14} />
        {t("entidades.darDeBaja")}
      </Button>
    </DialogoConfirmar>
  );
}
