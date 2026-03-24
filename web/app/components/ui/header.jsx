"use client"; // Necesario porque usamos componentes interactivos de Headless UI

import { useAuth } from "@/app/context/AuthContext";
import Image from "next/image";
import Link from "next/link";
import { Button } from "@/app/components/ui/button";
import { Menu, MenuButton, MenuItem, MenuItems } from "@headlessui/react";
import { useRouter } from "next/navigation";

export default function Header() {
  // TODO: Conectar esto con tu contexto de autenticación real más adelante.
  // Por ahora, cambia esto a 'true' para ver el menú de usuario logueado.
  const { user, loading ,logout } = useAuth();
  const router = useRouter();


  // Función de ejemplo para cerrar sesión
  const handleLogout = async () => {
    // Aquí iría la lógica para borrar cookies/tokens
    await logout();
    router.push("/auth/login"); // Redirige al login después de cerrar sesión
  };

const isLoggedIn = !!user; // Simula el estado de carga

if(loading) {
  return (
  <header className="z-50 flex h-16 w-full items-center justify-between bg-white/80 px-4 backdrop-blur-md sm:px-6 md:h-20 z-10 relative">
        <Link href="/" className="flex items-center gap-3">
          <Image src="/logo.svg" alt="Logo" width={36} height={36} priority />
          <span className="text-2xl font-bold text-gray-800">Codi</span>
        </Link>
      </header>
    );
}

  return (
    <header className="z-50 flex h-16 w-full items-center justify-between bg-white/80 px-4 backdrop-blur-md sm:px-6 md:h-20 z-10 relative">
      {/* LADO IZQUIERDO: Logo y Título */}
      <Link href="/" className="flex items-center gap-3">
        <Image src="/logo.svg" alt="Logo" width={36} height={36} priority />
        <span className="text-2xl font-bold text-gray-800">Codi</span>
      </Link>

      {/* LADO DERECHO: Condicional (Logueado vs No Logueado) */}
      <div className="flex items-center gap-4">
        {!isLoggedIn ? (
          // Vista para usuarios NO logueados (Tus botones originales)
          <>
            <Button asChild variant="outline" className="btn-header-login">
              <Link href="/auth/login">Iniciar sesión</Link>
            </Button>
            <Button asChild variant="outline" className="btn-header">
              <Link href="/auth/register">Registrarse</Link>
            </Button>
          </>
        ) : (
          // Vista para usuarios LOGUEADOS (Menú con Headless UI)
          <>
            {/* Dropdown del perfil de usuario */}
            <Menu as="div" className="relative ml-1">
              <MenuButton className="relative flex rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
                <span className="sr-only">Abrir menú de usuario</span>
                <Image
                  alt="Avatar del usuario"
                  src="/usuario.png"
                  width={36}
                  height={36}
                  className="rounded-full border border-gray-200"
                />
              </MenuButton>

              <MenuItems
                transition
                className="absolute right-0 z-10 mt-2 w-48 origin-top-right rounded-md bg-white py-1 shadow-lg ring-1 ring-black/5 transition focus:outline-none data-[closed]:scale-95 data-[closed]:transform data-[closed]:opacity-0 data-[enter]:duration-100 data-[enter]:ease-out data-[leave]:duration-75 data-[leave]:ease-in"
              >
                <MenuItem>
                  {({ active }) => (
                    <Link
                      href="/auth/user"
                      className={`block px-4 py-2 text-sm ${active ? "bg-gray-100 text-gray-900" : "text-gray-700"}`}>
                      Tu perfil
                    </Link>
                  )}
                </MenuItem>
                <MenuItem>
                  {({ active }) => (
                    <button
                      onClick={handleLogout}
                      className={`block w-full text-left px-4 py-2 text-sm ${active ? "bg-red-50 text-red-700" : "text-gray-700"}`}
                    >
                      Cerrar sesión
                    </button>
                  )}
                </MenuItem>
              </MenuItems>
            </Menu>
          </>
        )}
      </div>
    </header>
  );
}