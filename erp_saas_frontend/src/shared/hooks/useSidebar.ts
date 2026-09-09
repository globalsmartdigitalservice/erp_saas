import { useCallback, useState } from "react";



const CLAVE = "erp.sidebar.colapsado";

function leerColapsado(): boolean {
  try {
    return localStorage.getItem(CLAVE) === "1";
  } catch {

    return false;
  }
}

export function useSidebar() {
  const [colapsado, setColapsado] = useState<boolean>(leerColapsado);
  const [abiertoEnMovil, setAbiertoEnMovil] = useState(false);

  const alternarColapsado = useCallback(() => {
    setColapsado((actual) => {
      const siguiente = !actual;
      try {
        localStorage.setItem(CLAVE, siguiente ? "1" : "0");
      } catch {

      }
      return siguiente;
    });
  }, []);

  const cerrarEnMovil = useCallback(() => setAbiertoEnMovil(false), []);
  const abrirEnMovil = useCallback(() => setAbiertoEnMovil(true), []);

  return {
    colapsado,
    alternarColapsado,
    abiertoEnMovil,
    abrirEnMovil,
    cerrarEnMovil,
    setAbiertoEnMovil,
  };
}
