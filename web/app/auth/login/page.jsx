"use client";

import { useState } from "react";
import Link from "next/link"; 
import { useRouter } from "next/navigation"; 
import { Button } from "@/app/components/ui/button"; 
import axios from "axios";
import Image from "next/image"; // Importamos Image para poner el logo de Codi
import { sileo } from "sileo";
import { Eye, EyeOff } from "lucide-react";
import { useAuth } from "@/app/context/AuthContext";

export default function Login()
 {
  const { setUser } = useAuth();
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);

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

  const [input, setInput] = useState({
    email: "",
    password: "",
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

  const isInvalidCredentialsError = (err) => {
    if (!axios.isAxiosError(err)) return false;

    const status = err.response?.status;
    const detail = (err.response?.data?.detail || "").toString().toLowerCase();
    const message = (err.response?.data?.message || "").toString().toLowerCase();

    return (
      status === 401 ||
      status === 403 ||
      detail.includes("credenciales") ||
      detail.includes("incorrect") ||
      message.includes("credenciales") ||
      message.includes("incorrect")
    );
  };

  const handleSuccess = (msg) => {
    sileo.success({
      title: "Inicio de sesión correcto",
      description: msg || "Bienvenido de nuevo.",
    });
    console.log("Éxito:", msg);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post("/backend/api/login", {
        email: input.email,
        password: input.password,
      }, { withCredentials: true });

      // Cargamos los datos del usuario desde /api/me
      const { data } = await axios.get("/backend/api/me", { withCredentials: true });
      setUser(data);

      handleSuccess("Bienvenido de nuevo!!");
      setTimeout(() => router.push("/"), 1000);
    } catch (error) {
      if (isInvalidCredentialsError(error)) {
        setInput({ email: "", password: "" });
      }
      handleError(error);
    }
    
  };

  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center p-6 bg-gray-100">
      
      {/* Contenedor de la Tarjeta (Card) */}
      <div className="w-full max-w-md bg-white p-8 rounded-2xl shadow-lg border border-gray-100">
        
        {/* Cabecera de la tarjeta con logo */}
        <div className="flex flex-col items-center mb-8">
          <Image src="/logo.svg" alt="Logo de Codi" width={48} height={48} priority className="mb-4" />
          <h1 className="text-3xl font-bold text-gray-900">
            Bienvenido a Codi
          </h1>
          <p className="text-sm text-gray-500 mt-2">Inicia sesión en tu cuenta para continuar</p>
        </div>
        
        <form onSubmit={handleSubmit} className="flex flex-col gap-5"> 
          
          {/* Grupo de Email con Label */}
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-gray-700" htmlFor="email">
              Correo electrónico *
            </label>
            <input 
              id="email"
              className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all" 
              type="email"
              name="email"
              value={input.email}
              onChange={handleChange}
              required
            />
          </div>

          {/* Grupo de Contraseña con Label */}
          <div className="flex flex-col gap-1.5 relative">
            <label className="text-sm font-medium text-gray-700" htmlFor="password">
              Contraseña *
            </label>

            <input 
              id="password"
              type={showPassword ? "text" : "password"}
              name="password"
              value={input.password}
              onChange={handleChange}
              className="w-full p-3 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
              required
            />

            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-[38px] text-gray-500"
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>

          {/* Botones */}
          <div className="flex flex-col gap-3 mt-4">
           <button 
              type="submit" 
              className="btn-codi-animated mt-4">
              Iniciar sesión
          </button>

            <Button asChild variant="outline" type="button" className="w-full py-2.5 rounded-lg">
              <Link href="/">Cancelar</Link>
            </Button>
          </div>

          {/* Enlace al registro */}
          <p className="mt-4 text-sm text-gray-600 text-center">
            ¿No tienes una cuenta? <Link href="/auth/register" className="text-blue-600 font-semibold hover:underline">Regístrate aquí</Link>.
          </p>

          {/*Enlace de "Olvidé mi contraseña"  */}
          <p className="mt-4 text-sm text-gray-600 text-center">
            <Link href="/auth/forgot-password" className="text-blue-600 font-semibold hover:underline">
              ¿Olvidaste tu contraseña?
            </Link>
          </p>
        </form>
      </div>
    </main>
  );
}