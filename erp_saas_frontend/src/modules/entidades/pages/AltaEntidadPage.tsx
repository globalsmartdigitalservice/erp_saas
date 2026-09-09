import { useMutation } from "@apollo/client";
import { ArrowLeft } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import {
  FormularioEntidad,
  type DatosDeEntidad,
} from "@/modules/entidades/components/FormularioEntidad";
import { CREAR_ENTIDAD } from "@/modules/entidades/graphql/entidades.mutations";
import { ENTIDADES } from "@/modules/entidades/graphql/entidades.queries";
import { Button } from "@/shared/components/ui/button";
import { mensajeDeError } from "@/shared/lib/errores";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/shared/components/ui/card";

/** Alta de una entidad. */
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
      <Button asChild variant="ghost" size="sm" className="-ml-2 gap-2">
        <Link to="..">
          <ArrowLeft size={16} />
          {t("entidades.volver")}
        </Link>
      </Button>

      <Card>
        <CardHeader>
          <CardTitle>{t("entidades.nueva")}</CardTitle>
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
