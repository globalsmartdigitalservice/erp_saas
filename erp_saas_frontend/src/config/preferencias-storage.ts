
export const CLAVES = {
  empresa: "erp.empresaId",
  idiomaId: "erp.idiomaId",
  idiomaCodigo: "erp.idiomaCodigo",
} as const;

function leer(clave: string): string | null {
  try {
    return localStorage.getItem(clave);
  } catch {
    return null;
  }
}

function escribir(clave: string, valor: string): void {
  try {
    localStorage.setItem(clave, valor);
  } catch {

  }
}

export function empresaGuardada(): string | null {
  return leer(CLAVES.empresa);
}

export function guardarEmpresa(empresaId: string): void {
  escribir(CLAVES.empresa, empresaId);
}

/** El ID del idioma, que es lo que espera la cabecera `X-Idioma`. */
export function idiomaGuardado(): string | null {
  return leer(CLAVES.idiomaId);
}

export function idiomaCodigoGuardado(): string | null {
  return leer(CLAVES.idiomaCodigo);
}

export function guardarIdioma(idiomaId: string, codigo: string): void {
  escribir(CLAVES.idiomaId, idiomaId);
  escribir(CLAVES.idiomaCodigo, codigo);
}
