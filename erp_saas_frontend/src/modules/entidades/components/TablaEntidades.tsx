import { AlertTriangle, Users } from "lucide-react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import {
  nombreCompleto,
  type Entidad,
} from "@/modules/entidades/types/entidad.types";
import {
  EstadoError,
  EstadoVacio,
  FilaEstadoTabla,
  FilasEsqueleto,
} from "@/shared/components/EstadosTabla";
import { Badge } from "@/shared/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/components/ui/table";


const COLUMNAS = 5;

type Props = {
  entidades: Entidad[];
  cargando: boolean;
  error?: boolean;
  onReintentar?: () => void;
};

export function TablaEntidades({
  entidades,
  cargando,
  error,
  onReintentar,
}: Props) {
  const { t } = useTranslation();

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>{t("entidades.nombre")}</TableHead>
            <TableHead>{t("entidades.tipo")}</TableHead>
            <TableHead>{t("entidades.documento")}</TableHead>
            <TableHead>{t("entidades.tipoDocumento")}</TableHead>
            <TableHead>{t("entidades.estado")}</TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          {cargando ? (
            <FilasEsqueleto columnas={COLUMNAS} />
          ) : error ? (
            <FilaEstadoTabla colSpan={COLUMNAS}>
              <EstadoError icono={AlertTriangle} onReintentar={onReintentar} />
            </FilaEstadoTabla>
          ) : entidades.length === 0 ? (
            <FilaEstadoTabla colSpan={COLUMNAS}>
              <EstadoVacio
                icono={Users}
                titulo={t("entidades.sinEntidades")}
                descripcion={t("entidades.sinEntidadesAyuda")}
              />
            </FilaEstadoTabla>
          ) : (
            entidades.map((entidad) => (
              <TableRow key={entidad.id}>
                <TableCell className="font-medium">
                  <Link
                    to={entidad.id}
                    className="hover:underline"
                  >
                    {nombreCompleto(entidad)}
                  </Link>
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {entidad.tipoEntidad?.nombre ?? "—"}
                </TableCell>
                <TableCell>
     
                  {entidad.documento || (
                    <span className="text-muted-foreground">
                      {t("entidades.sinDocumento")}
                    </span>
                  )}
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {entidad.tipoDocumento?.nombre ?? "—"}
                </TableCell>
                <TableCell>
                  {entidad.estado && (
                    <Badge variant="secondary">{entidad.estado.nombre}</Badge>
                  )}
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}
