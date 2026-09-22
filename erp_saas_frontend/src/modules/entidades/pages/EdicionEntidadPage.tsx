import { useMutation, useQuery } from "@apollo/client";
import { AlertTriangle } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import {
  FormularioEntidad,
  type DatosDeEntidad,
} from "@/modules/entidades/components/FormularioEntidad";
import { ACTUALIZAR_ENTIDAD } from "@/modules/entidades/graphql/entidades.mutations";
import {
  ENTIDAD,
  ENTIDADES,
} from "@/modules/entidades/graphql/entidades.queries";
import type { Entidad } from "@/modules/entidades/types/entidad.types";
import { BackButton } from "@/shared/components/BackButton";
import { PageTitle } from "@/shared/components/PageTitle";
import { ErrorState, EmptyState } from "@/shared/components/TableStates";
import { Card, CardContent, CardHeader } from "@/shared/components/ui/card";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { mensajeDeError } from "@/shared/lib/errores";

export function EdicionEntidadPage() {
  const { t } = useTranslation();
  const navegar = useNavigate();
  const { id } = useParams<{ id: string }>();

  const consulta = useQuery<{ entidad: Entidad | null }>(ENTIDAD, {
    variables: { id },
    skip: !id,
  });

  const [actualizar, { loading: guardando, error }] = useMutation(
    ACTUALIZAR_ENTIDAD,
    { refetchQueries: [ENTIDAD, ENTIDADES] },
  );

  const entidad = consulta.data?.entidad ?? null;

  async function guardar(datos: DatosDeEntidad) {
    const resultado = await actualizar({
      variables: {
        id,
        datos: {
          tipoEntidadId: datos.tipoEntidadId,
          nombre: datos.nombre.trim(),
          priApellido: datos.priApellido.trim(),
          segApellido: datos.segApellido.trim(),
          tipoDocumentoId: datos.tipoDocumentoId,
          documento: datos.documento.trim(),
          regimenTributarioId: datos.regimenTributarioId,
          estadoId: datos.estadoId,
        },
      },
    });

    if (!resultado.data?.actualizarEntidad) return;

    toast.success(t("entidades.guardada"));
    navegar("..");
  }

  if (consulta.loading) {
    return <Skeleton className="h-96 w-full" />;
  }

  if (consulta.error && entidad === null) {
    return (
      <ErrorState error={consulta.error} onRetry={() => consulta.refetch()} />
    );
  }

  if (entidad === null) {
    return (
      <EmptyState
        icon={AlertTriangle}
        title={t("entidades.noExiste")}
        description={t("entidades.noExisteAyuda")}
      />
    );
  }

  return (
    <section className="space-y-4">
      <BackButton>{t("entidades.volver")}</BackButton>

      <Card>
        <CardHeader>
          <PageTitle>
            {t("entidades.editar")}
          </PageTitle>
        </CardHeader>
        <CardContent>
          <FormularioEntidad
            inicial={{
              tipoEntidadId: entidad.tipoEntidad?.id ?? null,
              nombre: entidad.nombre,
              priApellido: entidad.priApellido,
              segApellido: entidad.segApellido,
              tipoDocumentoId: entidad.tipoDocumento?.id ?? null,
              documento: entidad.documento,
              regimenTributarioId: entidad.regimenTributario?.id ?? null,
              estadoId: entidad.estado?.id ?? null,
            }}
            guardando={guardando}
            error={mensajeDeError(error, t) ?? null}
            onGuardar={guardar}
            onCancelar={() => navegar("..")}
          />
        </CardContent>
      </Card>
    </section>
  );
}
