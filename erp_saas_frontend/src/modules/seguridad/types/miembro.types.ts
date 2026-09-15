export type RolDeMiembro = {
  id: string;
  nombre: string;
};

export type PersonaDeMiembro = {
  id: string;
  username: string;
  email: string;
  nombreCompleto: string;
  isActive: boolean;
  debeCambiarPassword: boolean;
};

export type Miembro = {
  id: string;
  estadoId: string;
  fechaAsignacion: string;
  usuario: PersonaDeMiembro | null;
  roles: RolDeMiembro[];
};

export type FiltroDeEstado = "activos" | "baja" | "todos";

export type PersonaEncontrada = {
  usuarioId: string;
  nombreCompleto: string;
  trabajaAca: boolean;
};

export type RolAsignable = {
  id: string;
  nombre: string;
  esHeredado: boolean;
};

export type DatosDePersonaNueva = {
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  segApellido: string;
  password: string | null;
};

export type AltaDeMiembro = {
  membresia: {
    id: string;
    usuario: Pick<PersonaDeMiembro, "id" | "username" | "nombreCompleto"> | null;
  };
  passwordTemporal: string | null;
};
