import { useState } from "react";
import { useTranslation } from "react-i18next";

import { ErrorAlert } from "@/shared/components/ErrorAlert";
import { SaveButton } from "@/shared/components/SaveButton";
import { SelectorDeTipologia } from "@/shared/components/SelectorDeTipologia";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { useEstadoActivoId } from "@/shared/hooks/useEstadoActivoId";
import { useTipologias } from "@/shared/hooks/useTipologias";

export type DatosDeEntidad = {
  tipoEntidadId: string | null;
  nombre: string;
  priApellido: string;
  segApellido: string;
  tipoDocumentoId: string | null;
  documento: string;
  regimenTributarioId: string | null;
  estadoId: string | null;
};

export const ENTIDAD_VACIA: DatosDeEntidad = {
  tipoEntidadId: null,
  nombre: "",
  priApellido: "",
  segApellido: "",
  tipoDocumentoId: null,
  documento: "",
  regimenTributarioId: null,
  estadoId: null,
};

type Props = {
  /** Sin `inicial` es un alta. */
  inicial?: DatosDeEntidad;
  guardando: boolean;
  error?: string | null;
  onGuardar: (datos: DatosDeEntidad) => void;
  onCancelar: () => void;
};

export function FormularioEntidad({
  inicial,
  guardando,
  error,
  onGuardar,
  onCancelar,
}: Props) {
  const { t } = useTranslation();
  const [datos, setDatos] = useState<DatosDeEntidad>(inicial ?? ENTIDAD_VACIA);
  const activoId = useEstadoActivoId();
  const estados = useTipologias("ESTADO_REGISTRO");

  // Sin el id de Activo resuelto, el alta muestra el campo para no quedar trabada.
  const esAlta = inicial === undefined;
  const debeMostrarEstado = !esAlta || (!estados.cargando && activoId === null);
  const estadoId = debeMostrarEstado ? datos.estadoId : activoId;

  const cambiar = (campo: keyof DatosDeEntidad, valor: string | null) =>
    setDatos((actual) => ({ ...actual, [campo]: valor }));

  const estaCompleto =
    datos.nombre.trim() !== "" &&
    datos.tipoEntidadId !== null &&
    datos.tipoDocumentoId !== null &&
    estadoId !== null;

  return (
    <form
      className="space-y-4"
      onSubmit={(e) => {
        e.preventDefault();
        if (estaCompleto && !guardando) onGuardar({ ...datos, estadoId });
      }}
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="tipoEntidad" obligatorio>{t("entidades.tipo")}</Label>
          <SelectorDeTipologia
            id="tipoEntidad"
            codigo="TIPO_ENTIDAD"
            valor={datos.tipoEntidadId}
            onCambiar={(v) => cambiar("tipoEntidadId", v)}
            placeholder={t("entidades.elegiTipo")}
          />
        </div>

        {debeMostrarEstado && (
          <div className="space-y-1.5">
            <Label htmlFor="estado" obligatorio>{t("entidades.estado")}</Label>
            <SelectorDeTipologia
              id="estado"
              codigo="ESTADO_REGISTRO"
              valor={datos.estadoId}
              onCambiar={(v) => cambiar("estadoId", v)}
              placeholder={t("entidades.elegiEstado")}
            />
          </div>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="space-y-1.5">
          <Label htmlFor="nombre" obligatorio>{t("entidades.nombreORazon")}</Label>
          <Input
            id="nombre"
            value={datos.nombre}
            onChange={(e) => cambiar("nombre", e.target.value)}
            autoFocus
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="priApellido">{t("entidades.priApellido")}</Label>
          <Input
            id="priApellido"
            value={datos.priApellido}
            onChange={(e) => cambiar("priApellido", e.target.value)}
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="segApellido">{t("entidades.segApellido")}</Label>
          <Input
            id="segApellido"
            value={datos.segApellido}
            onChange={(e) => cambiar("segApellido", e.target.value)}
          />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="space-y-1.5">
          <Label htmlFor="tipoDocumento" obligatorio>{t("entidades.tipoDocumento")}</Label>
          <SelectorDeTipologia
            id="tipoDocumento"
            codigo="TIPO_DOCUMENTO"
            valor={datos.tipoDocumentoId}
            onCambiar={(v) => cambiar("tipoDocumentoId", v)}
            placeholder={t("entidades.elegiTipoDocumento")}
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="documento">{t("entidades.documento")}</Label>
          <Input
            id="documento"
            aria-describedby="documento-ayuda"
            value={datos.documento}
            onChange={(e) => cambiar("documento", e.target.value)}
          />
          <p id="documento-ayuda" className="text-xs text-muted-foreground">
            {t("entidades.documentoAyuda")}
          </p>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="regimen">{t("entidades.regimenTributario")}</Label>
          <SelectorDeTipologia
            id="regimen"
            codigo="REGIMEN_TRIBUTARIO"
            opcional
            valor={datos.regimenTributarioId}
            onCambiar={(v) => cambiar("regimenTributarioId", v)}
            placeholder={t("entidades.elegiRegimenTributario")}
          />
          <p className="text-xs text-muted-foreground">
            {t("entidades.regimenTributarioAyuda")}
          </p>
        </div>
      </div>

      <ErrorAlert message={error} />

      <div className="flex gap-2">
        <SaveButton isSaving={guardando} disabled={!estaCompleto}>
          {t("entidades.guardar")}
        </SaveButton>
        <Button type="button" variant="ghost" onClick={onCancelar} disabled={guardando}>
          {t("entidades.cancelar")}
        </Button>
      </div>
    </form>
  );
}
