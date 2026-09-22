import { useQuery } from "@apollo/client";
import { Plus, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { TablaMiembros } from "@/modules/seguridad/components/miembros/TablaMiembros";
import { MIEMBROS } from "@/modules/seguridad/graphql/miembros.queries";
import type {
  FiltroDeEstado,
  Miembro,
} from "@/modules/seguridad/types/miembro.types";
import { PageHeader } from "@/shared/components/PageHeader";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/shared/components/ui/tabs";
import { useTipologias } from "@/shared/hooks/useTipologias";
import { ABREV_ACTIVO, ABREV_BAJA } from "@/shared/types/tipologia.types";

const ABREVIATURA_POR_FILTRO: Record<FiltroDeEstado, string | null> = {
  activos: ABREV_ACTIVO,
  baja: ABREV_BAJA,
  todos: null,
};

export function ListaMiembrosPage() {
  const { t } = useTranslation();
  const [filtro, setFiltro] = useState<FiltroDeEstado>("activos");
  const [texto, setTexto] = useState("");
  const estados = useTipologias("ESTADO_REGISTRO");

  const abreviatura = ABREVIATURA_POR_FILTRO[filtro];
  const estadoId = abreviatura
    ? (estados.opciones.find((estado) => estado.abreviatura === abreviatura)?.id ?? null)
    : null;
  const esperandoEstado = abreviatura !== null && estadoId === null;

  const { data, loading, error, refetch } = useQuery<{ miembros: Miembro[] }>(
    MIEMBROS,
    { variables: { estadoId }, skip: esperandoEstado },
  );

  const nombresDeEstado = useMemo(
    () => new Map(estados.opciones.map((estado) => [estado.id, estado.nombre])),
    [estados.opciones],
  );

  const miembros = useMemo(
    () => filtrarPorTexto(data?.miembros ?? [], texto),
    [data, texto],
  );

  return (
    <section className="space-y-4">
      <PageHeader
        title={t("miembros.titulo")}
        description={t("miembros.ayuda")}
        action={
          <Button asChild className="gap-2">
            <Link to="nuevo">
              <Plus aria-hidden="true" />
              {t("miembros.nuevo")}
            </Link>
          </Button>
        }
      />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <Tabs value={filtro} onValueChange={(valor) => setFiltro(valor as FiltroDeEstado)}>
          <TabsList>
            <TabsTrigger value="activos">{t("miembros.filtroActivos")}</TabsTrigger>
            <TabsTrigger value="baja">{t("miembros.filtroBaja")}</TabsTrigger>
            <TabsTrigger value="todos">{t("miembros.filtroTodos")}</TabsTrigger>
          </TabsList>
        </Tabs>

        <div className="flex w-full items-center gap-3 sm:w-auto">
          {data && (
            <span className="shrink-0 text-sm tabular-nums text-muted-foreground">
              {t("miembros.cantidad", { count: miembros.length })}
            </span>
          )}
          <div className="relative w-full sm:w-72">
            <Search
              className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
              aria-hidden="true"
            />
            <Input
              type="search"
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              placeholder={t("miembros.buscar")}
              aria-label={t("miembros.buscar")}
              className="pl-8"
            />
          </div>
        </div>
      </div>

      <TablaMiembros
        miembros={miembros}
        nombresDeEstado={nombresDeEstado}
        cargando={loading || (esperandoEstado && estados.cargando)}
        error={error}
        buscando={texto.trim() !== ""}
        onReintentar={() => refetch()}
      />
    </section>
  );
}

function sinTildes(texto: string): string {
  return texto.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLocaleLowerCase();
}

function filtrarPorTexto(miembros: Miembro[], texto: string): Miembro[] {
  const buscado = sinTildes(texto.trim());
  if (!buscado) return miembros;

  return miembros.filter(({ usuario }) =>
    usuario
      ? [usuario.nombreCompleto, usuario.username, usuario.email].some((campo) =>
          sinTildes(campo).includes(buscado),
        )
      : false,
  );
}
