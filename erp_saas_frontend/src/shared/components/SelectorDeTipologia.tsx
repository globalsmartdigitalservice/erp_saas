import { useEffect } from "react";
import { useTranslation } from "react-i18next";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/components/ui/select";
import { useTipologias } from "@/shared/hooks/useTipologias";


const NINGUNA = "__ninguna__";

type Props = {

  codigo: string;
  valor: string | null;
  onCambiar: (id: string | null) => void;
  placeholder?: string;
  disabled?: boolean;

  predeterminada?: string;

  opcional?: boolean;
};

export function SelectorDeTipologia({
  codigo,
  valor,
  onCambiar,
  placeholder,
  disabled,
  predeterminada,
  opcional,
}: Props) {
  const { t } = useTranslation();
  const { opciones, cargando } = useTipologias(codigo);


  useEffect(() => {
    if (predeterminada === undefined || valor !== null) return;

    const opcion = opciones.find((o) => o.abreviatura === predeterminada);
    if (opcion !== undefined) onCambiar(opcion.id);
  }, [predeterminada, valor, opciones, onCambiar]);

  return (
    <Select
      value={valor ?? undefined}
      onValueChange={(elegido) =>
        onCambiar(elegido === NINGUNA ? null : elegido)
      }
      disabled={disabled || cargando || opciones.length === 0}
    >
      <SelectTrigger>
        <SelectValue
          placeholder={cargando ? t("comun.cargando") : placeholder}
        />
      </SelectTrigger>
      <SelectContent>
        {opcional && (
          <SelectItem value={NINGUNA}>{t("comun.ninguna")}</SelectItem>
        )}
        {opciones.map((opcion) => (
          <SelectItem key={opcion.id} value={opcion.id}>
            {opcion.nombre}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
