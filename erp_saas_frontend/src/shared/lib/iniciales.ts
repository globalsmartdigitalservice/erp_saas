/** Las iniciales de las dos primeras palabras: "Juan Carlos Pérez" → "JC". */
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
