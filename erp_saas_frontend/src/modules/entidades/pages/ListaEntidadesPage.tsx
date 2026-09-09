import { useQuery } from "@apollo/client";
import { Plus, Search, X } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { TablaEntidades } from "@/modules/entidades/components/TablaEntidades";
import {
  ENTIDADES,
  ENTIDAD_POR_DOCUMENTO,
} from "@/modules/entidades/graphql/entidades.queries";
import type {
  Entidad,
  Pagina,
} from "@/modules/entidades/types/entidad.types";
import { Paginacion } from "@/shared/components/Paginacion";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";


export function ListaEntidadesPage() {
  const { t } = useTranslation();

  const [desde, setDesde] = useState(0);
  const [textoBusqueda, setTextoBusqueda] = useState("");
  const [documentoBuscado, setDocumentoBuscado] = useState<string | null>(null);

  const lista = useQuery<{ entidades: Pagina<Entidad> }>(ENTIDADES, {
    variables: { limite: null, desde },
    skip: documentoBuscado !== null,
  });

  const busqueda = useQuery<{ entidadPorDocumento: Entidad | null }>(
    ENTIDAD_POR_DOCUMENTO,
    {
      variables: { documento: documentoBuscado },
      skip: documentoBuscado === null,
    },
  );

  const buscando = documentoBuscado !== null;

  const entidades = buscando
    ? busqueda.data?.entidadPorDocumento
      ? [busqueda.data.entidadPorDocumento]
      : []
    : (lista.data?.entidades.items ?? []);

  const info = lista.data?.entidades.info;

  function buscar() {
    const limpio = textoBusqueda.trim();

    setDocumentoBuscado(limpio === "" ? null : limpio);
    setDesde(0);
  }

  function limpiar() {
    setTextoBusqueda("");
    setDocumentoBuscado(null);
    setDesde(0);
  }

  return (
    <section className="space-y-4">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h1 className="font-heading text-xl font-semibold">
            {t("entidades.titulo")}
          </h1>
          <p className="text-sm text-muted-foreground">
            {t("entidades.ayuda")}
          </p>
        </div>

        <Button asChild className="gap-2">
          <Link to="nueva">
            <Plus size={16} />
            {t("entidades.nueva")}
          </Link>
        </Button>
      </header>

      <div className="flex gap-2">
        <Input
          value={textoBusqueda}
          onChange={(e) => setTextoBusqueda(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && buscar()}
          placeholder={t("entidades.buscarPorDocumento")}
          className="max-w-xs"
        />
        <Button variant="secondary" onClick={buscar} className="gap-2">
          <Search size={16} />
          {t("entidades.buscar")}
        </Button>
        {buscando && (
          <Button variant="ghost" onClick={limpiar} className="gap-2">
            <X size={16} />
            {t("entidades.limpiar")}
          </Button>
        )}
      </div>

      <TablaEntidades
        entidades={entidades}
        cargando={buscando ? busqueda.loading : lista.loading}
        error={Boolean(buscando ? busqueda.error : lista.error)}
        onReintentar={() =>
          buscando ? busqueda.refetch() : lista.refetch()
        }
      />


      {!buscando && info && (
        <Paginacion
          total={info.total}
          limite={info.limite}
          desde={info.desde}
          onCambiar={setDesde}
        />
      )}
    </section>
  );
}
