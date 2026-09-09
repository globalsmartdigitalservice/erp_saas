import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "@/shared/i18n/en.json";
import es from "@/shared/i18n/es.json";

import { idiomaCodigoGuardado } from "./preferencias-storage";


export const IDIOMA_POR_DEFECTO = "es";

i18n.use(initReactI18next).init({
  resources: {
    es: { translation: es },
    en: { translation: en },
  },
  lng: idiomaCodigoGuardado() || IDIOMA_POR_DEFECTO,
  fallbackLng: IDIOMA_POR_DEFECTO,
  interpolation: {

    escapeValue: false,
  },
});

export default i18n;
