"use client";
import Image from "next/image";
import { useAuth } from "@/app/context/AuthContext";
import { useTranslation } from "react-i18next";
import "@/lib/i18n";

export default function WelcomeScreen({ onSuggestionClick }) {
  const { user, loading } = useAuth();
  const { t } = useTranslation();

  // Sugerencias genericas. Antes estaban hardcodeadas por slug, pero los slugs
  // ahora dependen del nombre real de la asignatura del docente — el banco
  // siempre caia al fallback. Mejor 3 prompts neutros que sirven para cualquier
  // asignatura, traducidos via i18n.
  const sugerencias = [
    t("welcome_suggestion_1"),
    t("welcome_suggestion_2"),
    t("welcome_suggestion_3"),
  ];

  const handlePromptClick = (prompt) => {
    if (typeof onSuggestionClick === "function") {
      onSuggestionClick(prompt);
    }
  };

  return (
    <section className="w-full flex items-center justify-center px-6 py-6">
      <div className="w-full max-w-3xl text-center ">
        <Image src="/logo.svg" alt="Logo" width={60} height={50} priority className="mx-auto" />
        <h1 className="text-4xl font-bold text-blue-600">{t("welcome_title")}</h1>
        <p className="mt-4 text-lg text-gray-700">{t("welcome_subtitle")}</p>
        {!loading && !user && (
          <p className="mt-6 text-lg text-gray-700">{t("welcome_login_prompt")}</p>
        )}
        {!loading && user && (
          <div className="mt-8 grid w-full grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {sugerencias.map((prompt) => (
              <button
                key={prompt}
                onClick={() => handlePromptClick(prompt)}
                className="btn-suggestion"
              >
                {prompt}
              </button>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
