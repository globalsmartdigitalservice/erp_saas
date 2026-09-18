import { useQuery } from "@apollo/client";
import { Plus, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { DialogoRol } from "@/modules/seguridad/components/roles/DialogoRol";
import { TablaRoles } from "@/modules/seguridad/components/roles/TablaRoles";
import { ROLES } from "@/modules/seguridad/graphql/roles.queries";
import type { Rol } from "@/modules/seguridad/types/rol.types";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/shared/components/ui/tabs";
import { useTipologias } from "@/shared/hooks/useTipologias";
import { mensajeDeError } from "@/shared/lib/errores";
import { ABREV_ACTIVO, ABREV_BAJA } from "@/shared/types/tipologia.types";

type FiltroDeEstado = "activos" | "baja" | "todos";

const ABREVIATURA_POR_FILTRO: Record<FiltroDeEstado, string | null> = {
  activos: ABREV_ACTIVO,
  baja: ABREV_BAJA,
  todos: null,
};

const ROL_NUEVO = null;

export function ListaRolesPage() {
  const { t } = useTranslation();
  const [filtro, setFiltro] = useState<FiltroDeEstado>("activos");
  const [texto, setTexto] = useState("");
  const [enEdicion, setEnEdicion] = useState<Rol | null>(ROL_NUEVO);
  const [dialogoAbierto, setDialogoAbierto] = useState(false);
  const estados = useTipologias("ESTADO_REGISTRO");

  const abreviatura = ABREVIATURA_POR_FILTRO[filtro];
  const estadoId = abreviatura
    ? (estados.opciones.find((estado) => estado.abreviatura === abreviatura)?.id ?? null)
    : null;
  const esperandoEstado = abreviatura !== null && estadoId === null;

  const { data, loading, error, refetch } = useQuery<{ roles: Rol[] }>(ROLES, {
    variables: { estadoId },
    skip: esperandoEstado,
  });

  const nombresDeEstado = useMemo(
    () => new Map(estados.opciones.map((estado) => [estado.id, estado.nombre])),
    [estados.opciones],
  );

  const roles = useMemo(() => filtrarPorTexto(data?.roles ?? [], texto), [data, texto]);

  function abrir(rol: Rol | null) {
    setEnEdicion(rol);
    setDialogoAbierto(true);
  }

  return (
    <section className="space-y-4">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h1 className="font-heading text-xl font-semibold">{t("roles.titulo")}</h1>
          <p className="text-sm text-muted-foreground">{t("roles.ayuda")}</p>
        </div>

        <Button className="gap-2" onClick={() => abrir(ROL_NUEVO)}>
          <Plus size={16} aria-hidden="true" />
          {t("roles.nuevo")}
        </Button>
      </header>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <Tabs value={filtro} onValueChange={(valor) => setFiltro(valor as FiltroDeEstado)}>
          <TabsList>
            <TabsTrigger value="activos">{t("roles.filtroActivos")}</TabsTrigger>
            <TabsTrigger value="baja">{t("roles.filtroBaja")}</TabsTrigger>
            <TabsTrigger value="todos">{t("roles.filtroTodos")}</TabsTrigger>
          </TabsList>
        </Tabs>

        <div className="flex w-full items-center gap-3 sm:w-auto">
          {data && (
            <span className="shrink-0 text-sm tabular-nums text-muted-foreground">
              {t("roles.cantidad", { count: roles.length })}
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
              placeholder={t("roles.buscar")}
              aria-label={t("roles.buscar")}
              className="pl-8"
            />
          </div>
        </div>
      </div>

      <TablaRoles
        roles={roles}
        nombresDeEstado={nombresDeEstado}
        cargando={loading || (esperandoEstado && estados.cargando)}
        error={mensajeDeError(error, t)}
        buscando={texto.trim() !== ""}
        onReintentar={() => refetch()}
        onEditar={abrir}
      />

      {dialogoAbierto && (
        <DialogoRol rol={enEdicion} onCerrar={() => setDialogoAbierto(false)} />
      )}
    </section>
  );
}

function sinTildes(texto: string): string {
  return texto.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLocaleLowerCase();
}

function filtrarPorTexto(roles: Rol[], texto: string): Rol[] {
  const buscado = sinTildes(texto.trim());
  if (!buscado) return roles;

  return roles.filter((rol) => sinTildes(rol.nombre).includes(buscado));
}
