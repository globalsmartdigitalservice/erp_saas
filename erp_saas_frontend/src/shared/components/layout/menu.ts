import { Settings, UserCog, Users, type LucideIcon } from "lucide-react";

export type PantallaDeMenu = {
  ruta: string;
  clave: string;
};

export type ModuloDeMenu = {
  id: string;
  clave: string;
  icono: LucideIcon;
  pantallas: PantallaDeMenu[];
};

export type MenuLocation = {
  modulo: ModuloDeMenu;
  pantalla: PantallaDeMenu;
};

export const MENU: ModuloDeMenu[] = [
  {
    id: "entidades",
    clave: "menu.entidades",
    icono: Users,
    pantallas: [
      { ruta: "/entidades", clave: "menu.listaEntidades" },
      { ruta: "/entidades/categorias", clave: "menu.categorias" },
    ],
  },
  {
    id: "seguridad",
    clave: "menu.seguridad",
    icono: UserCog,
    pantallas: [
      { ruta: "/seguridad/usuarios", clave: "menu.usuarios" },
      { ruta: "/seguridad/roles", clave: "menu.roles" },
    ],
  },
  {
    id: "configuracion",
    clave: "menu.configuracion",
    icono: Settings,
    pantallas: [{ ruta: "/configuracion/listas", clave: "menu.listas" }],
  },
];

const MENU_LOCATIONS: MenuLocation[] = MENU.flatMap((modulo) =>
  modulo.pantallas.map((pantalla) => ({ modulo, pantalla })),
);

/**
 * La pantalla del menú a la que pertenece la URL. Gana la coincidencia más
 * larga: `/entidades/categorias` es Categorías, no Entidades, y `/entidades/5`
 * sí es Entidades.
 */
export function findMenuLocation(pathname: string): MenuLocation | null {
  const candidatas = MENU_LOCATIONS.filter(
    ({ pantalla }) =>
      pathname === pantalla.ruta || pathname.startsWith(pantalla.ruta + "/"),
  );

  return (
    candidatas.sort((a, b) => b.pantalla.ruta.length - a.pantalla.ruta.length)[0] ??
    null
  );
}
