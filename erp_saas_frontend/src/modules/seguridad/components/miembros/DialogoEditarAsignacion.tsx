import { useMutation } from "@apollo/client";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import { ACTUALIZAR_ASIGNACION } from "@/modules/seguridad/graphql/miembros.mutations";
import { MIEMBROS, ROLES_DE_MIEMBRO } from "@/modules/seguridad/graphql/miembros.queries";
import {
  fechaLegible,
  type CambiosDeAsignacion,
  type RolAsignadoDeMiembro,
} from "@/modules/seguridad/types/miembro.types";
import { ErrorAlert } from "@/shared/components/ErrorAlert";
import { SaveButton } from "@/shared/components/SaveButton";
import { Button } from "@/shared/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/components/ui/dialog";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/components/ui/select";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { Textarea } from "@/shared/components/ui/textarea";
import { useTipologias } from "@/shared/hooks/useTipologias";
import { mensajeDeError } from "@/shared/lib/errores";

const RECARGAR = { refetchQueries: [ROLES_DE_MIEMBRO, MIEMBROS] };
const LARGO_MAXIMO_DEL_MOTIVO = 200;

type Props = {
  asignacion: RolAsignadoDeMiembro;
  onCerrar: () => void;
};

export function DialogoEditarAsignacion({ asignacion, onCerrar }: Props) {
  return (
    <Dialog open onOpenChange={(abierto) => !abierto && onCerrar()}>
      <DialogContent className="sm:max-w-md">
        <FormularioAsignacion asignacion={asignacion} onCerrar={onCerrar} />
      </DialogContent>
    </Dialog>
  );
}

/**
 * Manda SOLO lo que cambió: la clave ausente es lo que el backend lee
 * como "no tocar". Una fecha de fin vacía viaja en `null`, que la borra.
 */
function cambiosDe(
  asignacion: RolAsignadoDeMiembro,
  fechaFin: string,
  motivo: string,
  estadoId: string,
): CambiosDeAsignacion {
  const cambios: CambiosDeAsignacion = {};
  const fechaNueva = fechaFin === "" ? null : fechaFin;

  if (fechaNueva !== asignacion.fechaFin) cambios.fechaFin = fechaNueva;
  if (motivo.trim() !== asignacion.motivo) cambios.motivo = motivo.trim();
  if (estadoId !== asignacion.estadoId) cambios.estadoId = estadoId;

  return cambios;
}

function FormularioAsignacion({ asignacion, onCerrar }: Props) {
  const { t, i18n } = useTranslation();
  const estados = useTipologias("ESTADO_REGISTRO");

  const [fechaFin, setFechaFin] = useState(asignacion.fechaFin ?? "");
  const [motivo, setMotivo] = useState(asignacion.motivo);
  const [estadoId, setEstadoId] = useState(asignacion.estadoId);

  const [actualizar, { loading, error }] = useMutation(ACTUALIZAR_ASIGNACION, RECARGAR);

  const cambios = cambiosDe(asignacion, fechaFin, motivo, estadoId);
  const puedeGuardar = Object.keys(cambios).length > 0 && !loading;

  async function guardar(evento: React.FormEvent) {
    evento.preventDefault();
    if (!puedeGuardar) return;

    const resultado = await actualizar({
      variables: { asignacionId: asignacion.id, datos: cambios },
    });
    if (!resultado.data?.actualizarAsignacion) return;

    toast.success(t("miembros.asignacionGuardada"));
    onCerrar();
  }

  return (
    <form onSubmit={guardar} className="space-y-4">
      <DialogHeader>
        <DialogTitle>{asignacion.rol?.nombre}</DialogTitle>
        <DialogDescription>
          {t("miembros.desdeFecha", {
            fecha: fechaLegible(asignacion.fechaInicio, i18n.language),
          })}
        </DialogDescription>
        <p className="text-xs text-muted-foreground">
          {t("miembros.editarAsignacionAyuda")}
        </p>
      </DialogHeader>

      <div className="space-y-2">
        <Label htmlFor="fecha-fin-asignacion">{t("miembros.fechaFin")}</Label>
        <Input
          id="fecha-fin-asignacion"
          type="date"
          value={fechaFin}
          min={asignacion.fechaInicio}
          onChange={(e) => setFechaFin(e.target.value)}
          aria-describedby="ayuda-de-la-fecha-fin"
        />
        <p id="ayuda-de-la-fecha-fin" className="text-xs text-muted-foreground">
          {t("miembros.fechaFinAyuda")}
        </p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="motivo-asignacion">{t("miembros.motivo")}</Label>
        <Textarea
          id="motivo-asignacion"
          rows={2}
          maxLength={LARGO_MAXIMO_DEL_MOTIVO}
          value={motivo}
          onChange={(e) => setMotivo(e.target.value)}
          placeholder={t("miembros.motivoEjemplo")}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="estado-asignacion">{t("miembros.estado")}</Label>
        {estados.cargando ? (
          <Skeleton className="h-9 w-full" />
        ) : (
          <Select value={estadoId} onValueChange={setEstadoId}>
            <SelectTrigger id="estado-asignacion">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {estados.opciones.map((estado) => (
                <SelectItem key={estado.id} value={estado.id}>
                  {estado.nombre}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      <ErrorAlert message={mensajeDeError(error, t)} />

      <DialogFooter>
        <Button type="button" variant="outline" onClick={onCerrar} disabled={loading}>
          {t("comun.cancelar")}
        </Button>
        <SaveButton isSaving={loading} disabled={!puedeGuardar}>
          {t("miembros.guardar")}
        </SaveButton>
      </DialogFooter>
    </form>
  );
}
