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

export type RolDeAsignacion = RolAsignable & {
  estadoId: string;
};

export type RolAsignadoDeMiembro = {
  id: string;
  fechaInicio: string;
  fechaFin: string | null;
  motivo: string;
  estadoId: string;
  rol: RolDeAsignacion | null;
};

export type CambiosDeAsignacion = {
  fechaFin?: string | null;
  motivo?: string;
  estadoId?: string;
};

export type EstadoDeAsignacion = "vigente" | "programada" | "rolDeBaja" | "terminada";

/**
 * Las cuatro condiciones son las mismas que exige el backend en
 * `_vigentes`: sin la del ROL, una asignación viva de un rol dado de baja
 * se vería igual que una que otorga, y no otorga nada.
 */
export function estadoDeAsignacion(
  asignacion: RolAsignadoDeMiembro,
  activoId: string | null,
  hoy: string = new Date().toLocaleDateString("sv-SE"),
): EstadoDeAsignacion {
  if (asignacion.estadoId !== activoId) return "terminada";
  if (asignacion.fechaFin !== null && asignacion.fechaFin < hoy) return "terminada";
  if (asignacion.rol !== null && asignacion.rol.estadoId !== activoId) return "rolDeBaja";
  if (asignacion.fechaInicio > hoy) return "programada";
  return "vigente";
}

/**
 * Si ocupa el rol, asignarlo de nuevo lo rechaza el backend.
 *
 * Mira SOLO la fecha de fin, igual que `hay_asignacion_vigente`: una
 * asignación dada de baja pero sin fecha de fin sigue ocupando el lugar,
 * aunque no esté vigente.
 */
export function ocupaElRol(asignacion: RolAsignadoDeMiembro): boolean {
  return asignacion.fechaFin === null;
}

export function fechaLegible(fecha: string, idioma: string): string {
  return new Date(`${fecha}T00:00:00`).toLocaleDateString(idioma, {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}
