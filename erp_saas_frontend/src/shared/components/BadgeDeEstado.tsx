import { Badge } from "@/shared/components/ui/badge";
import { cn } from "@/shared/lib/utils";

type Props = {
  estado: { id: string; nombre: string } | null;
  activoId: string | null;
};

/** Activo en verde; cualquier otro estado, apagado. */
export function BadgeDeEstado({ estado, activoId }: Props) {
  if (estado === null) return null;

  const esActivo = activoId !== null && estado.id === activoId;
  const esInactivo = activoId !== null && !esActivo;

  return (
    <Badge
      variant="outline"
      className={cn(
        "font-normal",
        esActivo && "border-primary/30 bg-primary/10 text-primary",
        esInactivo && "text-muted-foreground",
      )}
    >
      {estado.nombre}
    </Badge>
  );
}
