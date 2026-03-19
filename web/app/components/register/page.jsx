import { Button } from "@/app/components/ui/button";
import Link from "next/link";

export default function Register() {
  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center p-24 bg-gray-100">
      <h1 className="text-4xl font-bold text-green-600">Registrate en Codi</h1>
      <input
        className="mt-8 w-full max-w-md p-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
        placeholder="Nombre completo" type ="text" />
      
      <input
        className="mt-4 w-full max-w-md p-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
        placeholder="Dirección de correo electrónico" type="email" />

      <input
        className="mt-4 w-full max-w-md p-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
        placeholder="Contraseña" type="text" />

      <input 
      className="mt-4 w-full max-w-md p-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
      placeholder="Confirmar contraseña" type="text" />

      <input className="mt-4 w-full max-w-md p-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
      placeholder="Nivel del estudiante (principiante, intermedio, avanzado)" type="text"/>

      {/* Cambiado <button> normal por el <Button> de shadcn */}
      <Button className="mt-6 w-full max-w-md bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded">
        Registrarse
      </Button>

      {/* Botón de Cancelar que vuelve a la página principal ("/") */}
      <Button asChild variant="outline" className="mt-4 w-full max-w-md">
        <Link href="/">Cancelar</Link>
      </Button>
    
    </main>
  );
}
