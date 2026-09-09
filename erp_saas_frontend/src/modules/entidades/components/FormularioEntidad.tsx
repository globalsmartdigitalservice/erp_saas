import { useState } from "react";
import { useTranslation } from "react-i18next";

import { SelectorDeTipologia } from "@/shared/components/SelectorDeTipologia";
import { ABREV_ACTIVO } from "@/shared/types/tipologia.types";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";



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
  inicial?: DatosDeEntidad;
  guardando: boolean;
  error?: string | null;
  onGuardar: (datos: DatosDeEntidad) => void;
  onCancelar: () => void;
};

export function FormularioEntidad({
  inicial = ENTIDAD_VACIA,
  guardando,
  error,
  onGuardar,
  onCancelar,
}: Props) {
  const { t } = useTranslation();
  const [datos, setDatos] = useState<DatosDeEntidad>(inicial);

  const cambiar = (campo: keyof DatosDeEntidad, valor: string | null) =>
    setDatos((actual) => ({ ...actual, [campo]: valor }));


  const completo =
    datos.nombre.trim() !== "" &&
    datos.tipoEntidadId !== null &&
    datos.tipoDocumentoId !== null &&
    datos.estadoId !== null;

  return (
    <form
      className="space-y-4"
      onSubmit={(e) => {
        e.preventDefault();
        if (completo && !guardando) onGuardar(datos);
      }}
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="tipoEntidad" obligatorio>{t("entidades.tipo")}</Label>
          <SelectorDeTipologia
            codigo="TIPO_ENTIDAD"
            valor={datos.tipoEntidadId}
            onCambiar={(v) => cambiar("tipoEntidadId", v)}
            placeholder={t("entidades.elegiTipo")}
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="estado" obligatorio>{t("entidades.estado")}</Label>
          <SelectorDeTipologia
            codigo="ESTADO_REGISTRO"
            predeterminada={inicial.estadoId === null ? ABREV_ACTIVO : undefined}
            valor={datos.estadoId}
            onCambiar={(v) => cambiar("estadoId", v)}
            placeholder={t("entidades.elegiEstado")}
          />
        </div>
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
            value={datos.documento}
            onChange={(e) => cambiar("documento", e.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            {t("entidades.documentoAyuda")}
          </p>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="regimen">{t("entidades.regimenTributario")}</Label>
          <SelectorDeTipologia
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


      {error && (
        <p className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      <div className="flex gap-2">
        <Button type="submit" disabled={!completo || guardando}>
          {guardando ? t("comun.cargando") : t("entidades.guardar")}
        </Button>
        <Button type="button" variant="ghost" onClick={onCancelar}>
          {t("entidades.cancelar")}
        </Button>
      </div>
    </form>
  );
}
