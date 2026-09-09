import { Settings, Users, type LucideIcon } from "lucide-react";



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
    id: "configuracion",
    clave: "menu.configuracion",
    icono: Settings,
    pantallas: [{ ruta: "/configuracion/listas", clave: "menu.listas" }],
  },
];
