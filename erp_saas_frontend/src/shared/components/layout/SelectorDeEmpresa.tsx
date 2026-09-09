import { gql, useQuery } from "@apollo/client";
import { useTranslation } from "react-i18next";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/components/ui/select";
import { usePreferencias } from "@/shared/preferencias";



const EMPRESAS = gql`
  query Empresas {
    empresas {
      id
      razonSocial
      esMatriz
    }
  }
`;

type Empresa = {
  id: string;
  razonSocial: string;
  esMatriz: boolean;
};

export function SelectorDeEmpresa() {
  const { t } = useTranslation();
  const { empresaId, elegirEmpresa } = usePreferencias();
  const { data, loading } = useQuery<{ empresas: Empresa[] }>(EMPRESAS);

  const empresas = data?.empresas ?? [];

  return (
    <Select
      value={empresaId ?? undefined}
      onValueChange={elegirEmpresa}
      disabled={loading || empresas.length === 0}
    >
      <SelectTrigger className="w-[240px]" aria-label={t("cabecera.empresa")}>
        <SelectValue
          placeholder={loading ? t("comun.cargando") : t("cabecera.elegiEmpresa")}
        />
      </SelectTrigger>
      <SelectContent>
        {empresas.map((empresa) => (
          <SelectItem key={empresa.id} value={empresa.id}>
  
            {empresa.esMatriz ? "" : "— "}
            {empresa.razonSocial}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
