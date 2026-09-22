import { useMutation } from "@apollo/client";
import { KeyRound, Loader2, RotateCcw, UserMinus, UserX } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import { DialogoPasswordTemporal } from "@/modules/seguridad/components/miembros/DialogoPasswordTemporal";
import {
  DESACTIVAR_USUARIO,
  DESAFILIAR,
  REACTIVAR_MEMBRESIA,
  REACTIVAR_USUARIO,
  RESETEAR_PASSWORD,
} from "@/modules/seguridad/graphql/miembros.mutations";
import { DETALLE_MIEMBRO, MIEMBROS } from "@/modules/seguridad/graphql/miembros.queries";
import {
  fechaLegible,
  type CuentaDeMiembro,
  type MembresiaDeMiembro,
} from "@/modules/seguridad/types/miembro.types";
import { BadgeDeEstado } from "@/shared/components/BadgeDeEstado";
import { ConfirmDialog } from "@/shared/components/ConfirmDialog";
import { Button } from "@/shared/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/shared/components/ui/card";
import { useEstadoId } from "@/shared/hooks/useEstadoId";
import { useTipologias } from "@/shared/hooks/useTipologias";
import { useSession } from "@/shared/session";
import { ABREV_ACTIVO, ABREV_BAJA } from "@/shared/types/tipologia.types";

const RECARGAR = { refetchQueries: [DETALLE_MIEMBRO, MIEMBROS] };

const CLASE_BOTON_DE_BAJA =
  "w-full justify-start gap-2 text-muted-foreground hover:bg-destructive/10 hover:text-destructive";

type Props = {
  cuenta: CuentaDeMiembro;
  membresia: MembresiaDeMiembro;
};

export function MembresiaEnEmpresa({ cuenta, membresia }: Props) {
  const { t, i18n } = useTranslation();
  const { empresa } = useSession();
  const estados = useTipologias("ESTADO_REGISTRO");

  const activoId = useEstadoId(ABREV_ACTIVO).id;
  const bajaId = useEstadoId(ABREV_BAJA).id;
  const nombreDeEstado = estados.opciones.find((e) => e.id === membresia.estadoId)?.nombre;
  const estaActiva = membresia.estadoId === activoId;
  const nombre = cuenta.nombreCompleto || cuenta.username;
  const razonSocial = empresa?.razonSocial ?? "";

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">
            {t("miembros.enEstaEmpresa", { empresa: razonSocial })}
          </CardTitle>
          <CardDescription className="flex flex-wrap items-center gap-2">
            {nombreDeEstado && (
              <BadgeDeEstado
                estado={{ id: membresia.estadoId, nombre: nombreDeEstado }}
                activoId={activoId}
              />
            )}
            <span>
              {t("miembros.desdeFecha", {
                fecha: fechaLegible(membresia.fechaAsignacion, i18n.language),
              })}
            </span>
            {membresia.fechaFinalizacion && (
              <span>
                {t("miembros.hastaFecha", {
                  fecha: fechaLegible(membresia.fechaFinalizacion, i18n.language),
                })}
              </span>
            )}
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-1">
          {estaActiva && <RestablecerPassword membresiaId={membresia.id} nombre={nombre} />}

          {estaActiva ? (
            <BajaEnEmpresa
              membresiaId={membresia.id}
              bajaId={bajaId}
              nombre={nombre}
              empresa={razonSocial}
            />
          ) : (
            <ReactivarEnEmpresa membresiaId={membresia.id} activoId={activoId} />
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">{t("miembros.cuenta")}</CardTitle>
          <CardDescription>
            {cuenta.isActive
              ? t("miembros.cuentaActivaAyuda")
              : t("miembros.cuentaDesactivadaAyuda")}
          </CardDescription>
        </CardHeader>

        <CardContent>
          {cuenta.isActive ? (
            <DesactivarCuenta usuarioId={cuenta.id} nombre={nombre} />
          ) : (
            <ReactivarCuenta usuarioId={cuenta.id} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function RestablecerPassword({ membresiaId, nombre }: { membresiaId: string; nombre: string }) {
  const { t } = useTranslation();
  const [temporal, setTemporal] = useState<string | null>(null);

  const [resetear, mutacion] = useMutation<{ resetearPassword: string }>(
    RESETEAR_PASSWORD,
    RECARGAR,
  );

  return (
    <>
      <ConfirmDialog
        title={t("miembros.resetearTitulo", { nombre })}
        description={t("miembros.resetearAyuda")}
        confirmLabel={t("miembros.resetear")}
        mutation={mutacion}
        onConfirm={async () => {
          const resultado = await resetear({ variables: { datos: { membresiaId } } });
          const password = resultado.data?.resetearPassword;
          if (!password) return false;
          setTemporal(password);
        }}
      >
        <Button variant="ghost" size="sm" className="w-full justify-start gap-2">
          <KeyRound size={14} aria-hidden="true" />
          {t("miembros.resetear")}
        </Button>
      </ConfirmDialog>

      {temporal && (
        <DialogoPasswordTemporal
          nombre={nombre}
          password={temporal}
          onCerrar={() => setTemporal(null)}
        />
      )}
    </>
  );
}

function BajaEnEmpresa({
  membresiaId,
  bajaId,
  nombre,
  empresa,
}: {
  membresiaId: string;
  bajaId: string | null;
  nombre: string;
  empresa: string;
}) {
  const { t } = useTranslation();
  const [desafiliar, mutacion] = useMutation(DESAFILIAR, RECARGAR);

  return (
    <ConfirmDialog
      title={t("miembros.bajaTitulo", { nombre, empresa })}
      description={t("miembros.bajaAyuda")}
      confirmLabel={t("miembros.darDeBaja")}
      mutation={mutacion}
      successMessage={t("miembros.dadoDeBaja")}
      onConfirm={async () => {
        const resultado = await desafiliar({
          variables: { datos: { membresiaId, estadoBajaId: bajaId } },
        });
        if (!resultado.data?.desafiliar) return false;
      }}
    >
      <Button variant="ghost" size="sm" className={CLASE_BOTON_DE_BAJA} disabled={bajaId === null}>
        <UserMinus size={14} aria-hidden="true" />
        {t("miembros.darDeBaja")}
      </Button>
    </ConfirmDialog>
  );
}

function ReactivarEnEmpresa({
  membresiaId,
  activoId,
}: {
  membresiaId: string;
  activoId: string | null;
}) {
  const { t } = useTranslation();
  const [reactivar, { loading }] = useMutation(REACTIVAR_MEMBRESIA, RECARGAR);

  async function alReactivar() {
    const resultado = await reactivar({
      variables: { membresiaId, estadoActivoId: activoId },
    });
    if (resultado.errors?.length) {
      toast.error(resultado.errors.map((falla) => falla.message).join(" · "));
      return;
    }
    toast.success(t("miembros.membresiaReactivada"));
  }

  return (
    <Button
      variant="outline"
      size="sm"
      className="w-full justify-start gap-2"
      onClick={alReactivar}
      disabled={loading || activoId === null}
      aria-busy={loading || undefined}
    >
      {loading ? (
        <Loader2 className="size-3.5 animate-spin" aria-hidden="true" />
      ) : (
        <RotateCcw size={14} aria-hidden="true" />
      )}
      {loading ? t("comun.cargando") : t("miembros.reactivarMembresia")}
    </Button>
  );
}

function DesactivarCuenta({ usuarioId, nombre }: { usuarioId: string; nombre: string }) {
  const { t } = useTranslation();
  const [desactivar, mutacion] = useMutation(DESACTIVAR_USUARIO, RECARGAR);

  return (
    <ConfirmDialog
      title={t("miembros.desactivarTitulo", { nombre })}
      description={t("miembros.desactivarAyuda")}
      confirmLabel={t("miembros.desactivarCuenta")}
      mutation={mutacion}
      successMessage={t("miembros.cuentaDesactivada")}
      onConfirm={async () => {
        const resultado = await desactivar({ variables: { id: usuarioId } });
        if (!resultado.data?.desactivarUsuario) return false;
      }}
    >
      <Button variant="ghost" size="sm" className={CLASE_BOTON_DE_BAJA}>
        <UserX size={14} aria-hidden="true" />
        {t("miembros.desactivarCuenta")}
      </Button>
    </ConfirmDialog>
  );
}

function ReactivarCuenta({ usuarioId }: { usuarioId: string }) {
  const { t } = useTranslation();
  const [reactivar, { loading }] = useMutation(REACTIVAR_USUARIO, RECARGAR);

  async function alReactivar() {
    const resultado = await reactivar({ variables: { id: usuarioId } });
    if (resultado.errors?.length) {
      toast.error(resultado.errors.map((falla) => falla.message).join(" · "));
      return;
    }
    toast.success(t("miembros.cuentaReactivada"));
  }

  return (
    <Button
      variant="outline"
      size="sm"
      className="w-full justify-start gap-2"
      onClick={alReactivar}
      disabled={loading}
      aria-busy={loading || undefined}
    >
      {loading ? (
        <Loader2 className="size-3.5 animate-spin" aria-hidden="true" />
      ) : (
        <RotateCcw size={14} aria-hidden="true" />
      )}
      {loading ? t("comun.cargando") : t("miembros.reactivarCuenta")}
    </Button>
  );
}
