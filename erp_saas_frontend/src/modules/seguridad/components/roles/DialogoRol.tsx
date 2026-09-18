import { useMutation } from "@apollo/client";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import {
  ACTUALIZAR_ROL,
  CREAR_ROL,
} from "@/modules/seguridad/graphql/roles.mutations";
import { ROLES } from "@/modules/seguridad/graphql/roles.queries";
import type { RolSinConteo } from "@/modules/seguridad/types/rol.types";
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
import { useTipologias } from "@/shared/hooks/useTipologias";
import { mensajeDeError } from "@/shared/lib/errores";
import { ABREV_ACTIVO } from "@/shared/types/tipologia.types";

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
  const estados = useTipologias("ESTADO_REGISTRO");

  const [crear, creacion] = useMutation(CREAR_ROL, {
    refetchQueries: [ROLES],
  });
  const [actualizar, edicion] = useMutation(ACTUALIZAR_ROL, {
    refetchQueries: [ROLES],
  });

  const enCurso = creacion.loading || edicion.loading;
  const error = mensajeDeError(creacion.error ?? edicion.error, t);

  const estadoActivoId =
    estados.opciones.find((estado) => estado.abreviatura === ABREV_ACTIVO)?.id ?? null;

  const limpio = nombre.trim();
  const sinCambios = rol !== null && limpio === rol.nombre;
  const puedeGuardar =
    limpio !== "" && !sinCambios && !enCurso && (rol !== null || estadoActivoId !== null);

  async function guardar(evento: React.FormEvent) {
    evento.preventDefault();
    if (!puedeGuardar) return;

    try {
      if (rol) {
        await actualizar({ variables: { id: rol.id, datos: { nombre: limpio } } });
        toast.success(t("roles.actualizado", { nombre: limpio }));
      } else {
        await crear({
          variables: { datos: { nombre: limpio, estadoId: estadoActivoId } },
        });
        toast.success(t("roles.creado", { nombre: limpio }));
      }
      onCerrar();
    } catch {
      // El cartel del formulario ya muestra el error que devolvió el servidor.
    }
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

      {error && (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}

      <DialogFooter>
        <Button type="button" variant="outline" onClick={onCerrar} disabled={enCurso}>
          {t("roles.cancelar")}
        </Button>
        <Button type="submit" disabled={!puedeGuardar}>
          {enCurso ? t("roles.guardando") : t("roles.guardar")}
        </Button>
      </DialogFooter>
    </form>
  );
}
