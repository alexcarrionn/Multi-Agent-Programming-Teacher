"use client";
import Image from "next/image";

export default function WelcomeScreen({ onSuggestionClick }) {
  const handlePromptClick = (prompt) => {
    if (typeof onSuggestionClick === "function") {
      onSuggestionClick(prompt);
    }
  };

  return (
    <section className="flex-1 flex items-center justify-center px-6 py-10">
      <div className="w-full max-w-3xl text-center">
        <Image src="/logo.svg" alt="Logo" width={60} height={50} priority className="mx-auto" />
        <h1 className="text-4xl font-bold text-blue-600">Bienvenido a Codi</h1>
        <p className="mt-4 text-lg text-gray-700">
          Tu agente docente para aprender programacion paso a paso.
        </p>
      </div>
    </section>
  );
}
