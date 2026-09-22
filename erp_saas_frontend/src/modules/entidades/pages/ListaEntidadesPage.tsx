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
import { PageHeader } from "@/shared/components/PageHeader";
import { Pagination } from "@/shared/components/Pagination";
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
      <PageHeader
        title={t("entidades.titulo")}
        description={t("entidades.ayuda")}
        action={
          <Button asChild className="gap-2">
            <Link to="nueva">
              <Plus aria-hidden="true" />
              {t("entidades.nueva")}
            </Link>
          </Button>
        }
      />

      <form
        role="search"
        className="flex flex-wrap gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          buscar();
        }}
      >
        <Input
          type="search"
          value={textoBusqueda}
          onChange={(e) => setTextoBusqueda(e.target.value)}
          placeholder={t("entidades.buscarPorDocumento")}
          aria-label={t("entidades.buscarPorDocumento")}
          className="max-w-xs"
        />
        <Button type="submit" variant="secondary" className="gap-2">
          <Search aria-hidden="true" />
          {t("entidades.buscar")}
        </Button>
        {buscando && (
          <Button type="button" variant="ghost" onClick={limpiar} className="gap-2">
            <X aria-hidden="true" />
            {t("entidades.limpiar")}
          </Button>
        )}
      </form>

      <TablaEntidades
        entidades={entidades}
        cargando={buscando ? busqueda.loading : lista.loading}
        error={buscando ? busqueda.error : lista.error}
        onReintentar={() =>
          buscando ? busqueda.refetch() : lista.refetch()
        }
      />

      {!buscando && info && (
        <Pagination
          total={info.total}
          limit={info.limite}
          offset={info.desde}
          onChange={setDesde}
        />
      )}
    </section>
  );
}
