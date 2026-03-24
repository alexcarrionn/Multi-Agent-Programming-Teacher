"use client";
import Image from "next/image";
import { useAuth } from "@/app/context/AuthContext";

export default function WelcomeScreen({ onSuggestionClick }) {
  const { user, loading } = useAuth();

  const handlePromptClick = (prompt) => {
    if (typeof onSuggestionClick === "function") {
      onSuggestionClick(prompt);
    }
  };

  return (
    <section className="w-full flex items-center justify-center px-6 py-6">
      <div className="w-full max-w-3xl text-center ">
        <Image src="/logo.svg" alt="Logo" width={60} height={50} priority className="mx-auto" />
        <h1 className="text-4xl font-bold text-blue-600">Bienvenido a Codi</h1>
        <p className="mt-4 text-lg text-gray-700">
          Tu agente docente para aprender programacion paso a paso.
        </p>
        {/* Este campo solo se muestra si el usuario no ha iniciado sesión */}
        {!loading && !user && (
          <p className="mt-6 text-lg text-gray-700">
            Inicia sesión para comenzar a interactuar con Codi.
          </p>
        )}

        {/* Sugerencias de ejemplo si el usuario ha iniciado sesión */}
        {!loading && user && (
          <div className="mt-8 grid w-full grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <button
              onClick={() => handlePromptClick("¿Cómo puedo crear una función en C++?")}
              className="btn-suggestion"
            >
              ¿Cómo puedo crear una función en C++?
            </button>
            <button
              onClick={() => handlePromptClick("¿Qué es una variable en C++?")}
              className="btn-suggestion"
            >
              ¿Qué es una variable en C++?
            </button>
            <button
              onClick={() => handlePromptClick("¿Cómo puedo escribir un bucle for en C++?")}
              className="btn-suggestion"
            >
              ¿Cómo puedo escribir un bucle for en C++?
            </button>
          </div>
        )}

      </div>
    </section>
  );
}
