export type EmpresaDelUsuario = {
  membresiaId: string;
  empresaId: string;
  razonSocial: string;
  esMatriz: boolean;
};

export type UsuarioDeLaSesion = {
  id: string;
  nombreCompleto: string;
  debeCambiarPassword: boolean;
};

/**
 * `necesitaElegirEmpresa` en true significa que la persona trabaja en más de
 * una y todavía no eligió: no hay sesión abierta y `empresas` trae las
 * opciones.
 */
export type ResultadoLogin = {
  necesitaElegirEmpresa: boolean;
  usuario: UsuarioDeLaSesion | null;
  empresas: EmpresaDelUsuario[];
};

/** `identificador` es el nombre de usuario o el correo: el backend acepta los dos. */
export type Credenciales = {
  identificador: string;
  password: string;
};

export const CREDENCIALES_VACIAS: Credenciales = {
  identificador: "",
  password: "",
};

export type CambioDePassword = {
  passwordActual: string;
  passwordNueva: string;
};

export const CAMBIO_DE_PASSWORD_VACIO: CambioDePassword = {
  passwordActual: "",
  passwordNueva: "",
};
