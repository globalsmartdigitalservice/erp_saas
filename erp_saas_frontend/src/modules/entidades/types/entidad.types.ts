

export type InfoDePagina = {
  total: number;
  limite: number;
  desde: number;
  haySiguiente: boolean;
};

export type Pagina<T> = {
  items: T[];
  info: InfoDePagina;
};


export type Tipologia = {
  id: string;
  nombre: string;
};


export type Entidad = {
  id: string;
  nombre: string;
  priApellido: string;
  segApellido: string;
  documento: string;
  regimenTributario: Tipologia | null;
  tipoEntidad: Tipologia | null;
  tipoDocumento: Tipologia | null;
  estado: Tipologia | null;
  roles?: RolEntidad[];
  direcciones?: Direccion[];
  contactos?: ContactoEntidad[];
};

export type CategoriaEntidad = {
  id: string;
  nombre: string;
  descripcion: string;

  descuentoCategCliente: string;

  listaPrecioId: number | null;
  estado: Tipologia | null;
};

export type RolEntidad = {
  id: string;
  tipoRol: Tipologia | null;
  categoria: CategoriaEntidad | null;

  limiteCredito: string | null;
  estado: Tipologia | null;
};

export type Direccion = {
  id: string;
  tipo: Tipologia | null;
  calle: string;
  numero: string;
  descripcion: string;
  direccionTexto: string;
  estado: Tipologia | null;
};

export type ContactoEntidad = {
  id: string;
  nombre: string;
  cargo: string;
  email: string;
  telefono: string;
  estado: Tipologia | null;
};


export function nombreCompleto(entidad: Entidad): string {
  return [entidad.nombre, entidad.priApellido, entidad.segApellido]
    .filter(Boolean)
    .join(" ");
}
