
//  La empresa NO está acá: sale del token de la sesión. Estuvo mientras no
// había login, y se fue con él. La clave vieja `erp.empresaId` puede haber
// quedado en el navegador de quien lo usó antes; nada la lee, así que da
// igual.
export const CLAVES = {
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
