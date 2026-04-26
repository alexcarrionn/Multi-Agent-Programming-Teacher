"use client";
import Image from "next/image";
import { useAuth } from "@/app/context/AuthContext";
import { useTranslation } from "react-i18next";
import "@/lib/i18n";

const SUGERENCIAS = {
  Introduccion_programacion: [
    "¿Cómo puedo crear una función en C++?",
    "¿Qué es una variable en C++?",
    "¿Cómo puedo escribir un bucle for en C++?",
  ],
  programacion_orientada_a_objetos: [
    "¿Cómo puedo crear una clase en Java?",
    "¿Cómo funciona la herencia en Java?",
    "¿Cómo se definen los métodos en Java?",
  ],
  programacion_concurrente_y_distribuida: [
    "¿Qué es un hilo (thread) en Java?",
    "¿Cómo se usa un mutex para evitar condiciones de carrera?",
    "¿Qué diferencia hay entre concurrencia y paralelismo?",
  ],
  algoritmos_y_estructuras_de_datos_i: [
    "Explicame la representación de conjuntos mediante árboles",
    "¿Qué es el TAD diccionario?",
    "¿Cómo implementar un grafo?",
  ],
  algoritmos_y_estructuras_de_datos_ii: [
    "Explicame el algoritmo de divide y vencerás",
    "En que se basan los algoritmos voraces",
    "¿Qué es el BackTracking?",
  ],
  tecnologias_de_la_programacion: [
    "¿Cuáles son los tipos de abstracción?",
    "¿Cómo se define una estructura de datos enlazada arborescente general?",
    "¿Cómo se implementa un TDA Pila?",
  ],
  bases_de_datos: [
    "¿Qué es una clave primaria en SQL?",
    "¿Cómo se hace un JOIN entre dos tablas?",
    "¿Qué diferencia hay entre SQL y NoSQL?",
  ],
  aplicaciones_distribuidas: [
    "¿Qué es XML?",
    "¿Cómo funciona JSON?",
    "Explicame qué es un Servlet",
  ],
  tecnologias_de_desarrollo_del_software: [
    "De los patrones de comportamiento, ¿cuáles son los más comunes y para qué sirven?",
    "De los patrones de creación, ¿cuáles son los más comunes y para qué sirven?",
    "De los patrones estructurales, ¿cuáles son los más comunes y para qué sirven?",
  ],
  procesos_de_desarrollo_de_software: [
    "¿Qué son los datos semi-estructurados?",
    "¿Qué es UML y para qué se utiliza?",
    "¿Qué es un requisito funcional?",
  ],
};

const SUGGESTIONS = {
  Introduccion_programacion: [
    "How can I create a function in C++?",
    "What is a variable in C++?",
    "How can I write a for loop in C++?",
  ],
  programacion_orientada_a_objetos: [
    "How can I create a class in Java?",
    "How does inheritance work in Java?",
    "How are methods defined in Java?",
  ],
  programacion_concurrente_y_distribuida: [
    "What is a thread in Java?",
    "How do you use a mutex to avoid race conditions?",
    "What is the difference between concurrency and parallelism?",
  ],
  algoritmos_y_estructuras_de_datos_i: [
    "Explain set representation using trees",
    "What is the dictionary ADT?",
    "How do you implement a graph?",
  ],
  algoritmos_y_estructuras_de_datos_ii: [
    "Explain the divide and conquer algorithm",
    "What are greedy algorithms based on?",
    "What is BackTracking?",
  ],
  tecnologias_de_la_programacion: [
    "What are the types of abstraction?",
    "How is a general tree-linked data structure defined?",
    "How is a Stack ADT implemented?",
  ],
  bases_de_datos: [
    "What is a primary key in SQL?",
    "How do you do a JOIN between two tables?",
    "What is the difference between SQL and NoSQL?",
  ],
  aplicaciones_distribuidas: [
    "What is XML?",
    "How does JSON work?",
    "Explain what a Servlet is",
  ],
  tecnologias_de_desarrollo_del_software: [
    "Among behavioral patterns, which are the most common and what are they used for?",
    "Among creational patterns, which are the most common and what are they used for?",
    "Among structural patterns, which are the most common and what are they used for?",
  ],
  procesos_de_desarrollo_de_software: [
    "What is semi-structured data?",
    "What is UML and what is it used for?",
    "What is a functional requirement?",
  ],
};

export default function WelcomeScreen({ onSuggestionClick }) {
  const { user, loading } = useAuth();
  const { t, i18n } = useTranslation();
  const asignatura = user?.asignatura ?? "Introduccion_programacion";
  const banco = i18n.language === "en" ? SUGGESTIONS : SUGERENCIAS;
  const sugerencias = banco[asignatura] ?? banco["Introduccion_programacion"];

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
