// 1. Importamos Link de Next.js
import Link from "next/link"; 
import { Button } from "@/app/components/ui/button"; 

export default function Login() {
  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center p-24 bg-gray-100">
      <h1 className="text-4xl font-bold text-blue-600">
        Bienvenido a Codi
      </h1>
      
      {/* 2. Cambiamos textarea por input para el correo */}
      <input 
        className="mt-8 w-full max-w-md p-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" 
        placeholder="Dirección de correo electrónico" 
        type="email"
      />

      {/* Cambiamos textarea por input para la contraseña */}
      <input 
        className="mt-4 w-full max-w-md p-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" 
        placeholder="Contraseña" 
        type="password"
      />

      {/* Botón principal de Iniciar sesión */}
      <Button className="mt-6 w-full max-w-md bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
        Iniciar sesión
      </Button>

      {/* Botón de Cancelar que vuelve a la página principal ("/") */}
      <Button asChild variant="outline" className="mt-4 w-full max-w-md">
        <Link href="/">Cancelar</Link>
      </Button>

      {/* Usamos el componente Link para el registro */}
      <p className="mt-6 text-lg text-gray-700">
        ¿No tienes una cuenta? <Link href="/components/register" className="text-blue-600 hover:underline">Regístrate aquí</Link>.
      </p>

    </main>
  );
}