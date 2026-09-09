import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}


/**
 * NUEVA UTILIDAD DRY:
 * Convierte un string separado por comas en un array limpio de espacios.
 */
export function parseCommaSeparated(input: string): string[] {
  if (!input) return [];
  return input
    .split(',')
    .map(item => item.trim())
    .filter(Boolean);
}