import { useQuery } from "@apollo/client";
import { ListChecks } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router-dom";

import {
  DataTableBody,
  DataTableHeader,
  DataTableRow,
  DataTable,
} from "@/shared/components/DataTable";
import { PageHeader } from "@/shared/components/PageHeader";
import { ErrorState, EmptyState } from "@/shared/components/TableStates";
import { Badge } from "@/shared/components/ui/badge";
import { Label } from "@/shared/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/components/ui/select";
import { TableCell, TableHead } from "@/shared/components/ui/table";
import {
  AGRUPADORES,
  TIPOLOGIAS,
} from "@/shared/graphql/tipologias.queries";
import { cn } from "@/shared/lib/utils";
import {
  origenDe,
  type Agrupador,
  type OrigenDeTipologia,
  type Tipologia,
} from "@/shared/types/tipologia.types";

const COLUMNAS = 3;

const CLASE_POR_ORIGEN: Record<OrigenDeTipologia, string> = {
  propia: "border-primary/30 bg-primary/10 text-primary",
  heredada: "bg-transparent text-muted-foreground",
  deFabrica: "border-transparent bg-secondary text-secondary-foreground",
};

function leerAgrupador(crudo: string | null): number | null {
  const valor = Number(crudo);
  return crudo !== null && Number.isInteger(valor) ? valor : null;
}

export function ListasPage() {
  const { t } = useTranslation();
  const [parametros, setParametros] = useSearchParams();
  const agrupador = leerAgrupador(parametros.get("lista"));

  const listas = useQuery<{ agrupadores: Agrupador[] }>(AGRUPADORES);

  const valores = useQuery<{ tipologias: Tipologia[] }>(TIPOLOGIAS, {
    variables: { agrupador },
    skip: agrupador === null,
  });

  const filas = valores.data?.tipologias ?? [];

  return (
    <section className="space-y-4">
      <PageHeader title={t("listas.titulo")} description={t("listas.ayuda")} />

      {listas.error ? (
        <ErrorState error={listas.error} onRetry={() => listas.refetch()} />
      ) : (
        <div className="flex flex-col gap-1.5 sm:w-72">
          <Label htmlFor="lista">{t("listas.lista")}</Label>
          <Select
            value={agrupador === null ? undefined : String(agrupador)}
            onValueChange={(valor) =>
              setParametros({ lista: valor }, { replace: true })
            }
            disabled={listas.loading}
          >
            <SelectTrigger id="lista">
              <SelectValue
                placeholder={
                  listas.loading ? t("comun.cargando") : t("listas.elegiLista")
                }
              />
            </SelectTrigger>
            <SelectContent>
              {(listas.data?.agrupadores ?? []).map((lista) => (
                <SelectItem key={lista.valor} value={String(lista.valor)}>
                  {lista.nombre}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {agrupador === null ? (
        !listas.error && (
          <EmptyState icon={ListChecks} title={t("listas.sinElegir")} />
        )
      ) : (
        <div className="space-y-2">
          {valores.data && (
            <p className="text-sm text-muted-foreground">
              {t("listas.valores", { count: filas.length })}
            </p>
          )}

          <DataTable>
            <DataTableHeader>
              <TableHead>{t("listas.valor")}</TableHead>
              <TableHead>{t("listas.abreviatura")}</TableHead>
              <TableHead>{t("listas.origen")}</TableHead>
            </DataTableHeader>

            <DataTableBody
              columns={COLUMNAS}
              isLoading={valores.loading}
              error={valores.error}
              onRetry={() => valores.refetch()}
              isEmpty={filas.length === 0}
              empty={<EmptyState icon={ListChecks} title={t("listas.sinValores")} />}
            >
              {filas.map((fila, indice) => (
                <DataTableRow key={fila.id} index={indice}>
                  <TableCell className="font-medium">{fila.nombre}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {fila.abreviatura || "—"}
                  </TableCell>
                  <TableCell>
                    <BadgeDeOrigen origen={origenDe(fila)} />
                  </TableCell>
                </DataTableRow>
              ))}
            </DataTableBody>
          </DataTable>
        </div>
      )}
    </section>
  );
}

function BadgeDeOrigen({ origen }: { origen: OrigenDeTipologia }) {
  const { t } = useTranslation();

  return (
    <Badge variant="outline" className={cn("font-normal", CLASE_POR_ORIGEN[origen])}>
      {t(`listas.${origen}`)}
    </Badge>
  );
}
