import { useMutation } from "@apollo/client";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import {
  ACTUALIZAR_ROL,
  CREAR_ROL,
} from "@/modules/seguridad/graphql/roles.mutations";
import { ROLES } from "@/modules/seguridad/graphql/roles.queries";
import type { Rol, RolSinConteo } from "@/modules/seguridad/types/rol.types";
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
import { useEstadoActivoId } from "@/shared/hooks/useEstadoActivoId";
import { mensajeDeError } from "@/shared/lib/errores";

type Props = {
  rol: RolSinConteo | null;
  onCerrar: () => void;
};

export function DialogoRol({ rol, onCerrar }: Props) {
  return (
    <Dialog open onOpenChange={(abierto) => !abierto && onCerrar()}>
      <DialogContent className="sm:max-w-md">
        <FormularioRol rol={rol} onCerrar={onCerrar} />
      </DialogContent>
    </Dialog>
  );
}

function FormularioRol({ rol, onCerrar }: Props) {
  const { t } = useTranslation();
  const [nombre, setNombre] = useState(rol?.nombre ?? "");
  const estadoActivoId = useEstadoActivoId();

  const [crear, creacion] = useMutation<{ crearRol: Rol | null }>(CREAR_ROL, {
    refetchQueries: [ROLES],
  });
  const [actualizar, edicion] = useMutation<{ actualizarRol: Rol | null }>(ACTUALIZAR_ROL, {
    refetchQueries: [ROLES],
  });

  const enCurso = creacion.loading || edicion.loading;
  const error = mensajeDeError(creacion.error ?? edicion.error, t);

  const limpio = nombre.trim();
  const sinCambios = rol !== null && limpio === rol.nombre;
  const puedeGuardar =
    limpio !== "" && !sinCambios && !enCurso && (rol !== null || estadoActivoId !== null);

  async function guardar(evento: React.FormEvent) {
    evento.preventDefault();
    if (!puedeGuardar) return;

    // Con errorPolicy "all" un rechazo del backend no lanza: se sabe por `data`.
    if (rol) {
      const resultado = await actualizar({ variables: { id: rol.id, datos: { nombre: limpio } } });
      if (!resultado.data?.actualizarRol) return;
    } else {
      const resultado = await crear({
        variables: { datos: { nombre: limpio, estadoId: estadoActivoId } },
      });
      if (!resultado.data?.crearRol) return;
    }

    toast.success(
      rol ? t("roles.actualizado", { nombre: limpio }) : t("roles.creado", { nombre: limpio }),
    );
    onCerrar();
  }

  return (
    <form onSubmit={guardar} className="space-y-4">
      <DialogHeader>
        <DialogTitle>{rol ? t("roles.editarTitulo") : t("roles.crearTitulo")}</DialogTitle>
        <DialogDescription>
          {rol ? t("roles.editarAyuda") : t("roles.crearAyuda")}
        </DialogDescription>
      </DialogHeader>

      <div className="space-y-2">
        <Label htmlFor="nombre-del-rol">{t("roles.campoNombre")}</Label>
        <Input
          id="nombre-del-rol"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          placeholder={t("roles.campoNombrePlaceholder")}
          maxLength={80}
          autoFocus
          autoComplete="off"
          aria-describedby="ayuda-del-nombre"
        />
        <p id="ayuda-del-nombre" className="text-xs text-muted-foreground">
          {t("roles.campoNombreAyuda")}
        </p>
      </div>

      <ErrorAlert message={error} />

      <DialogFooter>
        <Button type="button" variant="outline" onClick={onCerrar} disabled={enCurso}>
          {t("roles.cancelar")}
        </Button>
        <SaveButton isSaving={enCurso} disabled={!puedeGuardar}>
          {t("roles.guardar")}
        </SaveButton>
      </DialogFooter>
    </form>
  );
}
