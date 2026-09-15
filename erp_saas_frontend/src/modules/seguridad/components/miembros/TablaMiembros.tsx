import {
  AlertTriangle,
  CircleAlert,
  KeyRound,
  UserX,
  Users,
  type LucideIcon,
} from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import {
  iniciales,
  type Miembro,
  type RolDeMiembro,
} from "@/modules/seguridad/types/miembro.types";
import {
  EstadoError,
  EstadoVacio,
  FilaEstadoTabla,
  FilasEsqueleto,
} from "@/shared/components/EstadosTabla";
import { Avatar, AvatarFallback } from "@/shared/components/ui/avatar";
import { Badge } from "@/shared/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/components/ui/table";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/shared/components/ui/tooltip";

const COLUMNAS = 4;
const RETRASO_POR_FILA_MS = 30;
const FILAS_ESCALONADAS = 12;

type Props = {
  miembros: Miembro[];
  nombresDeEstado: Map<string, string>;
  cargando: boolean;
  error?: string;
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

  return (
    <div className="overflow-hidden rounded-lg border bg-card">
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/40 hover:bg-muted/40">
            <TableHead>{t("miembros.persona")}</TableHead>
            <TableHead>{t("miembros.correo")}</TableHead>
            <TableHead>{t("miembros.roles")}</TableHead>
            <TableHead>{t("miembros.estado")}</TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          {cargando ? (
            <FilasEsqueleto columnas={COLUMNAS} />
          ) : error ? (
            <FilaEstadoTabla colSpan={COLUMNAS}>
              <EstadoError
                icono={AlertTriangle}
                mensaje={error}
                onReintentar={onReintentar}
              />
            </FilaEstadoTabla>
          ) : miembros.length === 0 ? (
            <FilaEstadoTabla colSpan={COLUMNAS}>
              <EstadoVacio
                icono={Users}
                titulo={buscando ? t("miembros.sinResultados") : t("miembros.sinMiembros")}
                descripcion={
                  buscando ? t("miembros.sinResultadosAyuda") : t("miembros.sinMiembrosAyuda")
                }
              />
            </FilaEstadoTabla>
          ) : (
            miembros.map((miembro, indice) => (
              <FilaMiembro
                key={miembro.id}
                miembro={miembro}
                estado={nombresDeEstado.get(miembro.estadoId)}
                indice={indice}
              />
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}

function FilaMiembro({
  miembro,
  estado,
  indice,
}: {
  miembro: Miembro;
  estado?: string;
  indice: number;
}) {
  const { t } = useTranslation();
  const persona = miembro.usuario;
  const nombre = persona?.nombreCompleto || persona?.username || "—";

  return (
    <TableRow
      className="motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-1 fill-mode-both"
      style={{
        animationDelay: `${Math.min(indice, FILAS_ESCALONADAS) * RETRASO_POR_FILA_MS}ms`,
      }}
    >
      <TableCell>
        <div className="flex items-center gap-3">
          <Avatar className="size-9">
            <AvatarFallback className="bg-primary/10 text-xs font-semibold text-primary">
              {iniciales(nombre)}
            </AvatarFallback>
          </Avatar>
          <div className="min-w-0">
            {persona ? (
              <Link to={persona.id} className="block truncate font-medium hover:underline">
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
        <RolesDeLaFila roles={miembro.roles} />
      </TableCell>

      <TableCell>
        <div className="flex flex-wrap items-center gap-1.5">
          {estado && <Badge variant="secondary">{estado}</Badge>}
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
    </TableRow>
  );
}

function RolesDeLaFila({ roles }: { roles: RolDeMiembro[] }) {
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
