import type { ApolloError } from "@apollo/client";
import type { TFunction } from "i18next";

/**
 * El texto que se le muestra al usuario cuando algo falla.
 *
 * El frontend NO escribe mensajes de error: los redacta el backend, que es
 * donde viven las reglas. La única excepción es cuando no hubo respuesta,
 * porque entonces no hay mensaje del backend que mostrar.
 *
 * Tampoco se muestra el texto crudo de Apollo: "Received status code 500"
 * no es un mensaje para un usuario, y le cuenta de más a quien esté
 * tanteando el sistema.
 */
export function mensajeDeError(
  error: ApolloError | undefined,
  t: TFunction,
): string | undefined {
  if (!error) return undefined;

  // Puede venir más de uno: GraphQL resuelve varios campos en la misma
  // petición y cada uno puede fallar por su cuenta.
  if (error.graphQLErrors.length > 0) {
    return error.graphQLErrors.map((falla) => falla.message).join(" · ");
  }

  if (import.meta.env.DEV) {
    console.error("[red] sin respuesta del backend:", error.networkError);
  }

  return t("comun.sinRespuesta");
}
