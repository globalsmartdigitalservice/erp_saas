import { useMutation, useQuery } from "@apollo/client";
import { AlertTriangle, ArrowLeft } from "lucide-react";
import { Link, useNavigate, useParams } from "react-router-dom";
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
import { EstadoVacio } from "@/shared/components/EstadosTabla";
import { Button } from "@/shared/components/ui/button";
import { mensajeDeError } from "@/shared/lib/errores";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/shared/components/ui/card";
import { Skeleton } from "@/shared/components/ui/skeleton";


export function EdicionEntidadPage() {
  const { t } = useTranslation();
  const navegar = useNavigate();
  const { id } = useParams<{ id: string }>();

  const { data, loading } = useQuery<{ entidad: Entidad | null }>(ENTIDAD, {
    variables: { id },
    skip: !id,
  });

  const [actualizar, { loading: guardando, error }] = useMutation(
    ACTUALIZAR_ENTIDAD,
    { refetchQueries: [ENTIDAD, ENTIDADES] },
  );

  const entidad = data?.entidad ?? null;

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

  if (loading) {
    return <Skeleton className="h-96 w-full" />;
  }

  if (entidad === null) {
    return (
      <EstadoVacio
        icono={AlertTriangle}
        titulo={t("entidades.noExiste")}
        descripcion={t("entidades.noExisteAyuda")}
      />
    );
  }

  return (
    <section className="space-y-4">
      <Button asChild variant="ghost" size="sm" className="-ml-2 gap-2">
        <Link to="..">
          <ArrowLeft size={16} />
          {t("entidades.volver")}
        </Link>
      </Button>

      <Card>
        <CardHeader>
          <CardTitle>{t("entidades.editar")}</CardTitle>
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
