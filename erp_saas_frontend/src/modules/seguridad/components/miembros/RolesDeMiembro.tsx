import { useMutation, useQuery } from "@apollo/client";
import { CircleAlert, History, Pencil, Plus, ShieldCheck, X } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import { DialogoEditarAsignacion } from "@/modules/seguridad/components/miembros/DialogoEditarAsignacion";
import { ASIGNAR_ROL, QUITAR_ROL } from "@/modules/seguridad/graphql/miembros.mutations";
import {
  MIEMBROS,
  ROLES_ASIGNABLES,
  ROLES_DE_MIEMBRO,
} from "@/modules/seguridad/graphql/miembros.queries";
import {
  estadoDeAsignacion,
  fechaLegible,
  ocupaElRol,
  type EstadoDeAsignacion,
  type RolAsignable,
  type RolAsignadoDeMiembro,
} from "@/modules/seguridad/types/miembro.types";
import { ConfirmDialog } from "@/shared/components/ConfirmDialog";
import { ErrorAlert } from "@/shared/components/ErrorAlert";
import { SaveButton } from "@/shared/components/SaveButton";
import { ErrorState } from "@/shared/components/TableStates";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/shared/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/shared/components/ui/dialog";
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
import { useEstadoId } from "@/shared/hooks/useEstadoId";
import { mensajeDeError } from "@/shared/lib/errores";
import { cn } from "@/shared/lib/utils";
import { ABREV_ACTIVO } from "@/shared/types/tipologia.types";

const RECARGAR = { refetchQueries: [ROLES_DE_MIEMBRO, MIEMBROS] };
const LARGO_MAXIMO_DEL_MOTIVO = 200;

type Props = {
  membresiaId: string;
  nombre: string;
};

export function RolesDeMiembro({ membresiaId, nombre }: Props) {
  const { t } = useTranslation();
  const [verTerminadas, setVerTerminadas] = useState(false);
  const { id: activoId, cargando: cargandoEstados } = useEstadoId(ABREV_ACTIVO);

  const { data, loading, error, refetch } = useQuery<{ rolesDe: RolAsignadoDeMiembro[] }>(
    ROLES_DE_MIEMBRO,
    { variables: { membresiaId } },
  );

  const asignaciones = (data?.rolesDe ?? []).map((asignacion) => ({
    asignacion,
    estado: estadoDeAsignacion(asignacion, activoId),
  }));
  const enCurso = asignaciones.filter((fila) => fila.estado !== "terminada");
  const terminadas = asignaciones.filter((fila) => fila.estado === "terminada");
  const visibles = verTerminadas ? [...enCurso, ...terminadas] : enCurso;

  const ocupados = (data?.rolesDe ?? [])
    .filter(ocupaElRol)
    .flatMap((asignacion) => (asignacion.rol ? [asignacion.rol.id] : []));

  return (
    <Card>
      <CardHeader className="flex-row items-start justify-between gap-4 space-y-0">
        <div className="space-y-1.5">
          <CardTitle className="text-base">{t("miembros.roles")}</CardTitle>
          <CardDescription>{t("miembros.rolesFichaAyuda")}</CardDescription>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {terminadas.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              className="gap-2 text-muted-foreground"
              onClick={() => setVerTerminadas(!verTerminadas)}
            >
              <History size={14} aria-hidden="true" />
              {verTerminadas
                ? t("miembros.ocultarTerminadas")
                : t("miembros.verTerminadas", { count: terminadas.length })}
            </Button>
          )}
          <DialogoAsignarRol membresiaId={membresiaId} ocupados={ocupados} activoId={activoId} />
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {loading || cargandoEstados ? (
          <Skeleton className="h-20 w-full" />
        ) : error ? (
          <ErrorState error={error} onRetry={() => refetch()} />
        ) : (
          <>
            {enCurso.length === 0 && (
              <div className="flex items-start gap-3 rounded-md border border-dashed p-4">
                <CircleAlert
                  className="mt-0.5 size-4 shrink-0 text-muted-foreground"
                  aria-hidden="true"
                />
                <div>
                  <p className="text-sm font-medium">{t("miembros.sinRol")}</p>
                  <p className="text-sm text-muted-foreground">{t("miembros.sinRolAyuda")}</p>
                </div>
              </div>
            )}

            {visibles.length > 0 && (
              <ul className="divide-y">
                {visibles.map((fila) => (
                  <FilaDeAsignacion
                    key={fila.asignacion.id}
                    asignacion={fila.asignacion}
                    estado={fila.estado}
                    nombre={nombre}
                  />
                ))}
              </ul>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

function FilaDeAsignacion({
  asignacion,
  estado,
  nombre,
}: {
  asignacion: RolAsignadoDeMiembro;
  estado: EstadoDeAsignacion;
  nombre: string;
}) {
  const { t, i18n } = useTranslation();
  const [editando, setEditando] = useState(false);

  return (
    <li
      className={cn(
        "flex items-center gap-3 py-3 first:pt-0 last:pb-0",
        (estado === "terminada" || estado === "rolDeBaja") && "opacity-60",
      )}
    >
      <span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
        <ShieldCheck size={16} aria-hidden="true" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate font-medium">{asignacion.rol?.nombre}</p>
        <p className="truncate text-xs text-muted-foreground">
          {t("miembros.desdeFecha", {
            fecha: fechaLegible(asignacion.fechaInicio, i18n.language),
          })}
          {asignacion.fechaFin &&
            ` · ${t("miembros.hastaFecha", {
              fecha: fechaLegible(asignacion.fechaFin, i18n.language),
            })}`}
          {asignacion.motivo && ` · ${asignacion.motivo}`}
        </p>
        {(estado !== "vigente" || asignacion.rol?.esHeredado) && (
          <div className="mt-1 flex flex-wrap gap-1">
            {estado === "programada" && (
              <Badge variant="outline" className="font-normal">
                {t("miembros.asignacionProgramada")}
              </Badge>
            )}
            {estado === "rolDeBaja" && (
              <Badge variant="outline" className="font-normal text-destructive">
                {t("miembros.asignacionRolDeBaja")}
              </Badge>
            )}
            {estado === "terminada" && (
              <Badge variant="outline" className="font-normal">
                {t("miembros.asignacionTerminada")}
              </Badge>
            )}
            {asignacion.rol?.esHeredado && (
              <Badge variant="outline" className="font-normal">
                {t("miembros.rolHeredado")}
              </Badge>
            )}
          </div>
        )}
      </div>

      <Button
        variant="ghost"
        size="icon"
        className="size-8 shrink-0 text-muted-foreground"
        aria-label={t("miembros.editarAsignacion")}
        title={t("miembros.editarAsignacion")}
        onClick={() => setEditando(true)}
      >
        <Pencil size={15} aria-hidden="true" />
      </Button>
      {ocupaElRol(asignacion) && <QuitarRol asignacion={asignacion} nombre={nombre} />}

      {editando && (
        <DialogoEditarAsignacion asignacion={asignacion} onCerrar={() => setEditando(false)} />
      )}
    </li>
  );
}

function QuitarRol({
  asignacion,
  nombre,
}: {
  asignacion: RolAsignadoDeMiembro;
  nombre: string;
}) {
  const { t } = useTranslation();
  const [quitar, mutacion] = useMutation(QUITAR_ROL, RECARGAR);
  const rol = asignacion.rol?.nombre ?? "";

  return (
    <ConfirmDialog
      title={t("miembros.quitarRolTitulo", { rol, nombre })}
      description={t("miembros.quitarRolAyuda")}
      confirmLabel={t("miembros.quitarRol")}
      mutation={mutacion}
      successMessage={t("miembros.rolQuitado")}
      onConfirm={async () => {
        const resultado = await quitar({ variables: { asignacionId: asignacion.id } });
        if (!resultado.data?.quitarRol) return false;
      }}
    >
      <Button
        variant="ghost"
        size="icon"
        className="size-8 shrink-0 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
        aria-label={t("miembros.quitarRol")}
        title={t("miembros.quitarRol")}
      >
        <X size={15} aria-hidden="true" />
      </Button>
    </ConfirmDialog>
  );
}

function DialogoAsignarRol({
  membresiaId,
  ocupados,
  activoId,
}: {
  membresiaId: string;
  ocupados: string[];
  activoId: string | null;
}) {
  const { t } = useTranslation();
  const [abierto, setAbierto] = useState(false);

  return (
    <Dialog open={abierto} onOpenChange={setAbierto}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="shrink-0 gap-2" disabled={activoId === null}>
          <Plus size={14} aria-hidden="true" />
          {t("miembros.asignarRol")}
        </Button>
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("miembros.asignarRol")}</DialogTitle>
          <DialogDescription>{t("miembros.asignarRolAyuda")}</DialogDescription>
        </DialogHeader>

        {activoId && (
          <FormularioAsignarRol
            membresiaId={membresiaId}
            ocupados={ocupados}
            activoId={activoId}
            onCerrar={() => setAbierto(false)}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}

function FormularioAsignarRol({
  membresiaId,
  ocupados,
  activoId,
  onCerrar,
}: {
  membresiaId: string;
  ocupados: string[];
  activoId: string;
  onCerrar: () => void;
}) {
  const { t } = useTranslation();
  const [rolId, setRolId] = useState("");
  const [motivo, setMotivo] = useState("");

  const roles = useQuery<{ roles: RolAsignable[] }>(ROLES_ASIGNABLES, {
    variables: { estadoId: activoId },
  });
  const disponibles = (roles.data?.roles ?? []).filter((rol) => !ocupados.includes(rol.id));

  const [asignar, { loading, error }] = useMutation(ASIGNAR_ROL, RECARGAR);

  async function guardar() {
    const resultado = await asignar({
      variables: {
        datos: { membresiaId, rolId, estadoId: activoId, motivo: motivo.trim() },
      },
    });
    if (!resultado.data?.asignarRol) return;

    toast.success(t("miembros.rolAsignado"));
    onCerrar();
  }

  return (
    <form
      className="grid gap-4"
      onSubmit={(e) => {
        e.preventDefault();
        if (rolId !== "" && !loading) void guardar();
      }}
    >
      <div className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="rol-a-asignar" obligatorio>{t("miembros.rol")}</Label>
          {roles.loading ? (
            <Skeleton className="h-9 w-full" />
          ) : disponibles.length === 0 ? (
            <p className="text-sm text-muted-foreground">{t("miembros.sinRolesParaAsignar")}</p>
          ) : (
            <Select value={rolId} onValueChange={setRolId}>
              <SelectTrigger id="rol-a-asignar">
                <SelectValue placeholder={t("miembros.elegiRol")} />
              </SelectTrigger>
              <SelectContent>
                {disponibles.map((rol) => (
                  <SelectItem key={rol.id} value={rol.id}>
                    {rol.nombre}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="motivo-rol">{t("miembros.motivo")}</Label>
          <Textarea
            id="motivo-rol"
            rows={2}
            maxLength={LARGO_MAXIMO_DEL_MOTIVO}
            value={motivo}
            onChange={(e) => setMotivo(e.target.value)}
            placeholder={t("miembros.motivoEjemplo")}
          />
        </div>

        <ErrorAlert message={mensajeDeError(error, t)} />
      </div>

      <DialogFooter>
        <Button type="button" variant="ghost" onClick={onCerrar} disabled={loading}>
          {t("comun.cancelar")}
        </Button>
        <SaveButton isSaving={loading} disabled={rolId === ""}>
          {t("miembros.asignar")}
        </SaveButton>
      </DialogFooter>
    </form>
  );
}
