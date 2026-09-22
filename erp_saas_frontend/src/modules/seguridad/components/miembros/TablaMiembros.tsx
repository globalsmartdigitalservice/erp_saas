import type { ApolloError } from "@apollo/client";
import {
  CircleAlert,
  KeyRound,
  UserX,
  Users,
  type LucideIcon,
} from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import type {
  Miembro,
  RolDeMiembro,
} from "@/modules/seguridad/types/miembro.types";
import { BadgeDeEstado } from "@/shared/components/BadgeDeEstado";
import {
  DataTableBody,
  DataTableHeader,
  DataTableRow,
  DataTable,
} from "@/shared/components/DataTable";
import { EmptyState } from "@/shared/components/TableStates";
import { Avatar, AvatarFallback } from "@/shared/components/ui/avatar";
import { Badge } from "@/shared/components/ui/badge";
import { TableCell, TableHead } from "@/shared/components/ui/table";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/shared/components/ui/tooltip";
import { useEstadoActivoId } from "@/shared/hooks/useEstadoActivoId";
import { iniciales } from "@/shared/lib/iniciales";

const COLUMNAS = 4;

type Props = {
  miembros: Miembro[];
  nombresDeEstado: Map<string, string>;
  cargando: boolean;
  error?: ApolloError;
  buscando: boolean;
  onReintentar: () => void;
};

export function TablaMiembros({
  miembros,
  nombresDeEstado,
  cargando,
  error,
  buscando,
  onReintentar,
}: Props) {
  const { t } = useTranslation();
  const activoId = useEstadoActivoId();

  return (
    <DataTable>
      <DataTableHeader>
        <TableHead>{t("miembros.persona")}</TableHead>
        <TableHead>{t("miembros.correo")}</TableHead>
        <TableHead>{t("miembros.roles")}</TableHead>
        <TableHead>{t("miembros.estado")}</TableHead>
      </DataTableHeader>

      <DataTableBody
        columns={COLUMNAS}
        isLoading={cargando}
        error={error}
        onRetry={onReintentar}
        isEmpty={miembros.length === 0}
        empty={
          <EmptyState
            icon={Users}
            title={buscando ? t("miembros.sinResultados") : t("miembros.sinMiembros")}
            description={
              buscando ? t("miembros.sinResultadosAyuda") : t("miembros.sinMiembrosAyuda")
            }
          />
        }
      >
        {miembros.map((miembro, indice) => (
          <FilaMiembro
            key={miembro.id}
            miembro={miembro}
            nombreDeEstado={nombresDeEstado.get(miembro.estadoId)}
            activoId={activoId}
            indice={indice}
          />
        ))}
      </DataTableBody>
    </DataTable>
  );
}

function FilaMiembro({
  miembro,
  nombreDeEstado,
  activoId,
  indice,
}: {
  miembro: Miembro;
  nombreDeEstado?: string;
  activoId: string | null;
  indice: number;
}) {
  const { t } = useTranslation();
  const persona = miembro.usuario;
  const nombre = persona?.nombreCompleto || persona?.username || "—";

  return (
    <DataTableRow index={indice} to={persona?.id}>
      <TableCell>
        <div className="flex items-center gap-3">
          <Avatar className="size-9">
            <AvatarFallback className="bg-primary/10 text-xs font-semibold text-primary">
              {iniciales(nombre)}
            </AvatarFallback>
          </Avatar>
          <div className="min-w-0">
            {persona ? (
              <Link
                to={persona.id}
                className="block truncate rounded-sm font-medium hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {nombre}
              </Link>
            ) : (
              <p className="truncate font-medium">{nombre}</p>
            )}
            {persona && (
              <p className="truncate text-xs text-muted-foreground">@{persona.username}</p>
            )}
          </div>
        </div>
      </TableCell>

      <TableCell className="text-muted-foreground">{persona?.email}</TableCell>

      <TableCell>
        <RolesDeFila roles={miembro.roles} />
      </TableCell>

      <TableCell>
        <div className="flex flex-wrap items-center gap-1.5">
          {nombreDeEstado && (
            <BadgeDeEstado
              estado={{ id: miembro.estadoId, nombre: nombreDeEstado }}
              activoId={activoId}
            />
          )}
          {persona && !persona.isActive && (
            <Marca icono={UserX} texto={t("miembros.cuentaDesactivada")} />
          )}
          {persona?.debeCambiarPassword && (
            <Marca
              icono={KeyRound}
              texto={t("miembros.passwordTemporal")}
              ayuda={t("miembros.passwordTemporalAyuda")}
            />
          )}
        </div>
      </TableCell>
    </DataTableRow>
  );
}

function RolesDeFila({ roles }: { roles: RolDeMiembro[] }) {
  const { t } = useTranslation();

  if (roles.length === 0) {
    return (
      <Marca
        icono={CircleAlert}
        texto={t("miembros.sinRol")}
        ayuda={t("miembros.sinRolAyuda")}
        punteada
      />
    );
  }

  return (
    <div className="flex flex-wrap gap-1.5">
      {roles.map((rol) => (
        <Badge key={rol.id} variant="outline" className="font-normal">
          {rol.nombre}
        </Badge>
      ))}
    </div>
  );
}

function Marca({
  icono: Icono,
  texto,
  ayuda,
  punteada = false,
}: {
  icono: LucideIcon;
  texto: string;
  ayuda?: string;
  punteada?: boolean;
}) {
  const marca = (
    <Badge
      variant="outline"
      tabIndex={ayuda ? 0 : undefined}
      className={`gap-1 font-normal text-muted-foreground ${punteada ? "border-dashed" : ""}`}
    >
      <Icono className="size-3" aria-hidden="true" />
      {texto}
    </Badge>
  );

  if (!ayuda) return marca;

  return (
    <Tooltip>
      <TooltipTrigger asChild>{marca}</TooltipTrigger>
      <TooltipContent>{ayuda}</TooltipContent>
    </Tooltip>
  );
}
