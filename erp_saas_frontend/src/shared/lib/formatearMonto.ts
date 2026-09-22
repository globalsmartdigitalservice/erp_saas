/** Un monto con dos decimales y el separador del idioma: "15.000,00" o "15,000.00". */
export function formatearMonto(
  valor: string | number | null | undefined,
  idioma: string,
): string {
  if (valor === null || valor === undefined || valor === "") return "";

  const numero = Number(valor);
  if (Number.isNaN(numero)) return String(valor);

  return new Intl.NumberFormat(idioma, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(numero);
}
