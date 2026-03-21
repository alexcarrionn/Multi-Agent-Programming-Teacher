"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/app/components/ui/button";
import axios from "axios";
import Image from "next/image";
import { sileo } from "sileo";

export default function Register() {
  const router = useRouter();

  const getErrorMessage = (err) => {
    if (!err) return "Ha ocurrido un error.";
    if (typeof err === "string") return err;
    if (axios.isAxiosError(err)) {
      return (
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "Error de red o del servidor."
      );
    }
    return "Ha ocurrido un error.";
  };

  // Estado unificado para todos los campos del registro
  const [input, setInput] = useState({
    nombre: "",
    email: "",
    password: "",
    confirmPassword: "",
    nivel: "", // principiante, intermedio, avanzado
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setInput({
      ...input,
      [name]: value,
    });
  };

  const handleError = (err) => {
    const description = getErrorMessage(err);
    sileo.error({
      title: "Error",
      description,
    });
    if (err) {
      console.error("Error:", err);
    }
  };

  const handleSuccess = (msg) => {
    sileo.success({
      title: "Registro completado",
      description: msg || "Tu cuenta se ha creado correctamente.",
    });
    console.log("Éxito:", msg);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Pequeña validación en el frontend antes de enviar
    if (input.password !== input.confirmPassword) {
      handleError("Las contraseñas no coinciden");
      return;
    }

    try {
      const { data } = await axios.post(
        "http://localhost:8000/api/register",
        {
          nombre: input.nombre,
          email: input.email,
          password: input.password,
          nivel: input.nivel,
        },
        { withCredentials: true }
      );

      const message = data?.message;
      handleSuccess(message || "Registro exitoso");
      setTimeout(() => {
        router.push("/auth/login"); // Redirigimos al login tras el registro
      }, 1500);
    } catch (error) {
      handleError(error);
    }

    // Limpiamos los campos (opcional si redirigimos rápido)
    setInput({
      nombre: "",
      email: "",
      password: "",
      confirmPassword: "",
      nivel: "",
    });
  };

  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center p-6 bg-gray-100 py-12">
      
      {/* Contenedor de la Tarjeta (Card) */}
      <div className="w-full max-w-md bg-white p-8 rounded-xl shadow-lg border border-gray-100">
        
        {/* Cabecera de la tarjeta con logo */}
        <div className="flex flex-col items-center mb-6">
          <Image src="/logo.svg" alt="Logo de Codi" width={48} height={48} priority className="mb-4" />
          <h1 className="text-3xl font-bold text-gray-900 text-center">
            Regístrate en Codi
          </h1>
          <p className="text-sm text-gray-500 mt-2 text-center">
            Crea tu cuenta y empieza a aprender
          </p>
        </div>
        
        <form onSubmit={handleSubmit} className="flex flex-col gap-4"> 
          
          {/* Grupo de Nombre Completo */}
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-gray-700" htmlFor="nombre">
              Nombre completo *
            </label>
            <input 
              id="nombre"
              className="w-full p-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm" 
              type="text"
              name="nombre"
              value={input.nombre}
              onChange={handleChange}
              required
            />
          </div>

          {/* Grupo de Email */}
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-gray-700" htmlFor="email">
              Correo electrónico *
            </label>
            <input 
              id="email"
              className="w-full p-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm" 
              type="email"
              name="email"
              value={input.email}
              onChange={handleChange}
              required
            />
          </div>

          {/* Grupo de Contraseñas*/}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-gray-700" htmlFor="password">
                Contraseña *
              </label>
              <input 
                id="password"
                className="w-full p-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm" 
                type="text"
                name="password"
                value={input.password}
                onChange={handleChange}
                required
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-gray-700" htmlFor="confirmPassword">
                Confirmar contraseña *
              </label>
              <input 
                id="confirmPassword"
                className="w-full p-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm" 
                type="text"
                name="confirmPassword"
                value={input.confirmPassword}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          {/* Grupo de Nivel del Estudiante (Select) */}
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-gray-700" htmlFor="nivel">
              Nivel de conocimiento *
            </label>
            <select
              id="nivel"
              name="nivel"
              value={input.nivel}
              onChange={handleChange}
              className="w-full p-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm bg-white"
              required
            >
              <option value="" disabled>Selecciona tu nivel...</option>
              <option value="principiante">Principiante</option>
              <option value="intermedio">Intermedio</option>
              <option value="avanzado">Avanzado</option>
            </select>
          </div>

          {/* Botones */}
          <div className="flex flex-col gap-3 mt-4">
            <Button 
              type="submit" 
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 rounded-lg shadow-sm transition-colors">

              Registrarse
            </Button>

            <Button asChild variant="outline" type="button" className="w-full py-2.5 rounded-lg">
              <Link href="/">Cancelar</Link>
            </Button>
          </div>

          {/* Enlace al login */}
          <p className="mt-2 text-sm text-gray-600 text-center">
            ¿Ya tienes una cuenta? <Link href="/auth/login" className="text-blue-600 font-semibold hover:underline">Inicia sesión</Link>.
          </p>
        </form>
      </div>
    </main>
  );
}