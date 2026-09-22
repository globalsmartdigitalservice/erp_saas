import { Loader2, LogOut } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { Avatar, AvatarFallback } from "@/shared/components/ui/avatar";
import { Button } from "@/shared/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/shared/components/ui/dropdown-menu";
import { iniciales } from "@/shared/lib/iniciales";
import { useSession } from "@/shared/session";

export function MenuDeUsuario() {
  const { t } = useTranslation();
  const { usuario, empresa, logout } = useSession();
  const [saliendo, setSaliendo] = useState(false);

  if (usuario === null) return null;

  async function cerrarSesion() {
    setSaliendo(true);
    try {
      await logout();
    } finally {
      setSaliendo(false);
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" className="gap-2 px-1.5 sm:pr-3">
          <Avatar className="size-7">
            <AvatarFallback className="bg-primary/10 text-xs font-semibold text-primary">
              {iniciales(usuario.nombreCompleto)}
            </AvatarFallback>
          </Avatar>
          <span className="hidden max-w-[160px] truncate sm:inline">
            {usuario.nombreCompleto}
          </span>
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="font-normal">
          <span className="block truncate">{usuario.nombreCompleto}</span>
          {empresa && (
            <span className="block truncate text-xs text-muted-foreground sm:hidden">
              {empresa.razonSocial}
            </span>
          )}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onSelect={(evento) => {
            // Sin esto el menú se cierra antes de que termine de salir.
            evento.preventDefault();
            void cerrarSesion();
          }}
          disabled={saliendo}
        >
          {saliendo ? (
            <Loader2 className="size-4 animate-spin" aria-hidden="true" />
          ) : (
            <LogOut className="size-4" aria-hidden="true" />
          )}
          {saliendo ? t("cabecera.saliendo") : t("cabecera.salir")}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
