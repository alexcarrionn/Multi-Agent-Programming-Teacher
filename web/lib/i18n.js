import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import es from "@/public/locales/es/common.json";
import en from "@/public/locales/en/common.json";

if (!i18n.isInitialized) {
  i18n.use(initReactI18next).init({
    resources: {
      es: { common: es },
      en: { common: en },
    },
    lng: "es",
    fallbackLng: "es",
    defaultNS: "common",
    interpolation: { escapeValue: false },
  });
}

export default i18n;
