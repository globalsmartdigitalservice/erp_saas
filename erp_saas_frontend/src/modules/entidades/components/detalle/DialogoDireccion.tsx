import { useMutation } from "@apollo/client";
import { Pencil, Plus } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import {
  ACTUALIZAR_DIRECCION,
  CREAR_DIRECCION,
} from "@/modules/entidades/graphql/entidades.mutations";
import { ENTIDAD } from "@/modules/entidades/graphql/entidades.queries";
import type { Direccion } from "@/modules/entidades/types/entidad.types";
import { SelectorDeTipologia } from "@/shared/components/SelectorDeTipologia";
import { ABREV_ACTIVO } from "@/shared/types/tipologia.types";
import { Button } from "@/shared/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/shared/components/ui/dialog";
import { Input } from "@/shared/components/ui/input";
import { mensajeDeError } from "@/shared/lib/errores";
import { Label } from "@/shared/components/ui/label";


export function DialogoDireccion({
  entidadId,
  direccion,
}: {
  entidadId: string;
  direccion?: Direccion;
}) {
  const { t } = useTranslation();
  const [abierto, setAbierto] = useState(false);
  const edicion = direccion !== undefined;

  return (
    <Dialog open={abierto} onOpenChange={setAbierto}>
      <DialogTrigger asChild>
        {edicion ? (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 shrink-0 text-muted-foreground hover:text-foreground"
            title={t("entidades.editarDireccion")}
          >
            <Pencil size={15} />
            <span className="sr-only">{t("entidades.editarDireccion")}</span>
          </Button>
        ) : (
          <Button variant="outline" size="sm" className="gap-2">
            <Plus size={14} />
            {t("entidades.agregarDireccion")}
          </Button>
        )}
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {edicion
              ? t("entidades.editarDireccion")
              : t("entidades.agregarDireccion")}
          </DialogTitle>
        </DialogHeader>

        <FormularioDireccion
          entidadId={entidadId}
          direccion={direccion}
          onCerrar={() => setAbierto(false)}
        />
      </DialogContent>
    </Dialog>
  );
}

function FormularioDireccion({
  entidadId,
  direccion,
  onCerrar,
}: {
  entidadId: string;
  direccion?: Direccion;
  onCerrar: () => void;
}) {
  const { t } = useTranslation();
  const edicion = direccion !== undefined;

  const [tipoId, setTipoId] = useState<string | null>(
    direccion?.tipo?.id ?? null,
  );
  const [estadoId, setEstadoId] = useState<string | null>(
    direccion?.estado?.id ?? null,
  );
  const [calle, setCalle] = useState(direccion?.calle ?? "");
  const [numero, setNumero] = useState(direccion?.numero ?? "");
  const [direccionTexto, setDireccionTexto] = useState(
    direccion?.direccionTexto ?? "",
  );
  const [descripcion, setDescripcion] = useState(direccion?.descripcion ?? "");

  const [guardarDireccion, { loading, error }] = useMutation(
    edicion ? ACTUALIZAR_DIRECCION : CREAR_DIRECCION,
    { refetchQueries: [ENTIDAD] },
  );

  async function guardar() {
    const campos = {
      tipoId,
      estadoId,
      calle: calle.trim(),
      numero: numero.trim(),
      direccionTexto: direccionTexto.trim(),
      descripcion: descripcion.trim(),
    };

    const resultado = await guardarDireccion({
      variables: edicion
        ? { id: direccion.id, datos: campos }
        : { datos: { entidadId, ...campos } },
    });

    const guardado =
      resultado.data?.crearDireccion ?? resultado.data?.actualizarDireccion;
    if (!guardado) return;

    toast.success(
      edicion
        ? t("entidades.direccionActualizada")
        : t("entidades.direccionAgregada"),
    );
    onCerrar();
  }

  return (
    <>
      <div className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label obligatorio>{t("entidades.tipo")}</Label>
            <SelectorDeTipologia
              codigo="TIPO_DIRECCION"
              valor={tipoId}
              onCambiar={setTipoId}
              placeholder={t("entidades.elegiTipo")}
            />
          </div>

          <div className="space-y-1.5">
            <Label obligatorio>{t("entidades.estado")}</Label>
            <SelectorDeTipologia
              codigo="ESTADO_REGISTRO"
              predeterminada={edicion ? undefined : ABREV_ACTIVO}
              valor={estadoId}
              onCambiar={setEstadoId}
              placeholder={t("entidades.elegiEstado")}
            />
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <div className="space-y-1.5 sm:col-span-2">
            <Label htmlFor="calle">{t("entidades.calleSola")}</Label>
            <Input
              id="calle"
              value={calle}
              onChange={(e) => setCalle(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="numero">{t("entidades.numero")}</Label>
            <Input
              id="numero"
              value={numero}
              onChange={(e) => setNumero(e.target.value)}
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="texto">{t("entidades.direccionTexto")}</Label>
          <Input
            id="texto"
            value={direccionTexto}
            onChange={(e) => setDireccionTexto(e.target.value)}
            placeholder={t("entidades.direccionTextoAyuda")}
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="referencia">{t("entidades.referencia")}</Label>
          <Input
            id="referencia"
            value={descripcion}
            onChange={(e) => setDescripcion(e.target.value)}
          />
        </div>

        {error && (
          <p className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
            {mensajeDeError(error, t)}
          </p>
        )}
      </div>

      <DialogFooter>
        <Button variant="ghost" onClick={onCerrar} disabled={loading}>
          {t("comun.cancelar")}
        </Button>
        <Button
          onClick={guardar}
          disabled={loading || tipoId === null || estadoId === null}
        >
          {loading ? t("comun.cargando") : t("entidades.guardar")}
        </Button>
      </DialogFooter>
    </>
  );
}
