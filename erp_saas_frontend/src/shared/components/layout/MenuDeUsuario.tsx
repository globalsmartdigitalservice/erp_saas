import { LogOut, User } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "@/shared/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/shared/components/ui/dropdown-menu";
import { useSession } from "@/shared/session";

export function MenuDeUsuario() {
  const { t } = useTranslation();
  const { usuario, logout } = useSession();
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
        <Button variant="ghost" size="sm" className="gap-2">
          <User className="size-4" aria-hidden="true" />
          <span className="hidden max-w-[160px] truncate sm:inline">
            {usuario.nombreCompleto}
          </span>
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="truncate font-normal">
          {usuario.nombreCompleto}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onSelect={(evento) => {
           
            evento.preventDefault();
            void cerrarSesion();
          }}
          disabled={saliendo}
        >
          <LogOut className="size-4" aria-hidden="true" />
          {saliendo ? t("cabecera.saliendo") : t("cabecera.salir")}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
