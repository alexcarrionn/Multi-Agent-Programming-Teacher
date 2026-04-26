"use client";

import { useState } from "react";
import { useAuth } from "@/app/context/AuthContext";
import Image from "next/image";
import Link from "next/link";
import { Button } from "@/app/components/ui/button";
import { Menu, MenuButton, MenuItem, MenuItems } from "@headlessui/react";
import { useRouter } from "next/navigation";
import { SelectorIdioma } from "@/app/components/ui/boton-idioma";
import { useTranslation } from "react-i18next";
import "@/lib/i18n";


const ASIGNATURAS = {
  Introduccion_programacion: "Introducción a la Programación",
  programacion_orientada_a_objetos: "Programación Orientada a Objetos",
  programacion_concurrente_y_distribuida: "Programación Concurrente y Distribuida",
  algoritmos_y_estructuras_de_datos_i: "Algoritmos y Estructuras de Datos I",
  algoritmos_y_estructuras_de_datos_ii: "Algoritmos y Estructuras de Datos II",
  tecnologias_de_la_programacion: "Tecnologías de la Programación",
  bases_de_datos: "Bases de Datos",
  aplicaciones_distribuidas: "Aplicaciones Distribuidas",
  tecnologias_de_desarrollo_del_software: "Tecnologías de Desarrollo del Software",
  procesos_de_desarrollo_de_software: "Procesos de Desarrollo de Software",
};

const SIGNATURES = {
  Introduccion_programacion: "Introduction to Programming",
  programacion_orientada_a_objetos: "Object-Oriented Programming",
  programacion_concurrente_y_distribuida: "Concurrent and Distributed Programming",
  algoritmos_y_estructuras_de_datos_i: "Algorithms and Data Structures I",
  algoritmos_y_estructuras_de_datos_ii: "Algorithms and Data Structures II",
  tecnologias_de_la_programacion: "Programming Technologies",
  bases_de_datos: "Databases",
  aplicaciones_distribuidas: "Distributed Applications",
  tecnologias_de_desarrollo_del_software: "Software Development Technologies",
  procesos_de_desarrollo_de_software: "Software Development Processes",
};

export default function Header() {
  const { user, loading, logout, setUser } = useAuth();
  const router = useRouter();
  const { t, i18n} = useTranslation();

  const [asignatura, setAsignatura] = useState("Introduccion_programacion");
  const asignaturas = Object.keys(ASIGNATURAS);

  const handleLogout = async () => {
    await logout();
    router.push("/auth/login");
  };

  const handleAsignaturaChange = async (e) => {
    const nueva = e.target.value;
    if (nueva === asignatura) return;
    setAsignatura(nueva);
    if (user) setUser({ ...user, asignatura: nueva });
  };

  const isLoggedIn = !!user;

  if (loading) {
    return (
      <header className="z-50 flex h-16 w-full items-center justify-between bg-white/80 px-4 backdrop-blur-md sm:px-6 md:h-20 relative">
        <Link href="/" className="flex items-center gap-3">
          <Image src="/logo.svg" alt="Logo" width={36} height={36} priority />
          <span className="text-2xl font-bold text-gray-800">Codi</span>
        </Link>
      </header>
    );
  }

  return (
    <header className="z-50 flex h-16 w-full items-center justify-between bg-white/80 px-4 backdrop-blur-md sm:px-6 md:h-20 relative">
      <Link href="/" className="flex items-center gap-3">
        <Image src="/logo.svg" alt="Logo" width={36} height={36} priority />
        <span className="text-2xl font-bold text-gray-800">Codi</span>
      </Link>

      <div className="flex items-center gap-3">
        {!isLoggedIn ? (
          <>
            <SelectorIdioma />
            <Button asChild variant="outline" className="btn-header-login">
              <Link href="/auth/login">{t("header_login")}</Link>
            </Button>
            <Button asChild variant="outline" className="btn-header">
              <Link href="/auth/register">{t("header_register")}</Link>
            </Button>
          </>
        ) : (
          <>
            <SelectorIdioma />
            <div className="relative">
              <select
                value={asignatura}
                onChange={handleAsignaturaChange}
                className="appearance-none rounded-xl border border-gray-200 bg-white/70 pl-4 pr-9 py-2 text-sm font-medium text-gray-700 shadow-sm cursor-pointer hover:border-blue-300 hover:bg-white focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all duration-150 max-w-[260px] truncate"
              >
                {asignaturas.map((id) => (
                  <option key={id} value={id}>
                     {(i18n.language === "en" ? SIGNATURES[id] : ASIGNATURAS[id]) ?? id.replace(/_/g, " ")}
                  </option>
                ))}
              </select>
              <span className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-gray-400">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </span>
            </div>

            <Menu as="div" className="relative">
              <MenuButton className="flex rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
                <span className="sr-only">{t("open_user_menu")}</span>
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
                      className={`block px-4 py-2 text-sm ${active ? "bg-gray-100 text-gray-900" : "text-gray-700"}`}
                    >
                      {t("header_profile")}
                    </Link>
                  )}
                </MenuItem>
                <MenuItem>
                  {({ active }) => (
                    <button
                      onClick={handleLogout}
                      className={`block w-full text-left px-4 py-2 text-sm ${active ? "bg-red-50 text-red-700" : "text-gray-700"}`}
                    >
                      {t("header_logout")}
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
