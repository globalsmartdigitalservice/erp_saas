import { useMutation } from "@apollo/client";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import {
  FormularioEntidad,
  type DatosDeEntidad,
} from "@/modules/entidades/components/FormularioEntidad";
import { CREAR_ENTIDAD } from "@/modules/entidades/graphql/entidades.mutations";
import { ENTIDADES } from "@/modules/entidades/graphql/entidades.queries";
import { BackButton } from "@/shared/components/BackButton";
import { PageTitle } from "@/shared/components/PageTitle";
import { Card, CardContent, CardHeader } from "@/shared/components/ui/card";
import { mensajeDeError } from "@/shared/lib/errores";

export function AltaEntidadPage() {
  const { t } = useTranslation();
  const navegar = useNavigate();

  const [crear, { loading, error }] = useMutation(CREAR_ENTIDAD, {
    refetchQueries: [ENTIDADES],
  });

  async function guardar(datos: DatosDeEntidad) {
    const resultado = await crear({
      variables: {
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

    const creada = resultado.data?.crearEntidad;
    if (!creada) return;

    toast.success(t("entidades.creada"));
    navegar(`../${creada.id}`);
  }

  return (
    <section className="space-y-4">
      <BackButton>{t("entidades.volver")}</BackButton>

      <Card>
        <CardHeader>
          <PageTitle>
            {t("entidades.nueva")}
          </PageTitle>
        </CardHeader>
        <CardContent>
          <FormularioEntidad
            guardando={loading}
            error={mensajeDeError(error, t) ?? null}
            onGuardar={guardar}
            onCancelar={() => navegar("..")}
          />
        </CardContent>
      </Card>
    </section>
  );
}
