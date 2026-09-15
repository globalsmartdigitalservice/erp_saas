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

export type CuentaDeMiembro = PersonaDeMiembro & {
  firstName: string;
  lastName: string;
  segApellido: string;
};

export type MembresiaDeMiembro = {
  id: string;
  fechaAsignacion: string;
  fechaFinalizacion: string | null;
  estadoId: string;
};

export type RolAsignadoDeMiembro = {
  id: string;
  fechaInicio: string;
  fechaFin: string | null;
  motivo: string;
  estadoId: string;
  rol: RolAsignable | null;
};

export function esVigente(
  asignacion: RolAsignadoDeMiembro,
  activoId: string | null,
  hoy: string = new Date().toLocaleDateString("sv-SE"),
): boolean {
  return (
    asignacion.estadoId === activoId &&
    asignacion.fechaInicio <= hoy &&
    (asignacion.fechaFin === null || asignacion.fechaFin >= hoy)
  );
}

export function fechaLegible(fecha: string, idioma: string): string {
  return new Date(`${fecha}T00:00:00`).toLocaleDateString(idioma, {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

export function iniciales(nombre: string): string {
  return (
    nombre
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((parte) => parte[0].toUpperCase())
      .join("") || "?"
  );
}
