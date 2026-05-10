"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/app/context/AuthContext";
import Image from "next/image";
import Link from "next/link";
import axios from "axios";
import { Button } from "@/app/components/ui/button";
import { Menu, MenuButton, MenuItem, MenuItems } from "@headlessui/react";
import { useRouter } from "next/navigation";
import { SelectorIdioma } from "@/app/components/ui/boton-idioma";
import { useTranslation } from "react-i18next";
import "@/lib/i18n";

const slugify = (nombre) => (nombre || "").toLowerCase().replace(/ /g, "_");

export default function Header() {
  const { user, loading, logout, setUser } = useAuth();
  const router = useRouter();
  const { t } = useTranslation();

  const [asignaturas, setAsignaturas] = useState([]);
  const [asignaturaSlug, setAsignaturaSlug] = useState("");

  const isAlumno = user?.rol === "alumno";

  useEffect(() => {
    if (!isAlumno) {
      setAsignaturas([]);
      return;
    }
    let cancelado = false;
    axios
      .get("/backend/api/me/asignaturas", { withCredentials: true })
      .then(({ data }) => {
        if (cancelado) return;
        const lista = data.asignaturas || [];
        setAsignaturas(lista);
        if (lista.length > 0) {
          const inicial = user?.asignatura || slugify(lista[0].nombre);
          setAsignaturaSlug(inicial);
          if (!user?.asignatura) setUser({ ...user, asignatura: inicial });
        }
      })
      .catch(() => {
        if (!cancelado) setAsignaturas([]);
      });
    return () => {
      cancelado = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAlumno, user?.alumno_id]);

  const handleLogout = async () => {
    await logout();
    router.push("/auth/login");
  };

  const handleAsignaturaChange = async (e) => {
    const nueva = e.target.value;
    if (nueva === asignaturaSlug) return;
    setAsignaturaSlug(nueva);
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
            {isAlumno && asignaturas.length > 0 && (
              <div className="relative">
                <select
                  value={asignaturaSlug}
                  onChange={handleAsignaturaChange}
                  className="appearance-none rounded-xl border border-gray-200 bg-white/70 pl-4 pr-9 py-2 text-sm font-medium text-gray-700 shadow-sm cursor-pointer hover:border-blue-300 hover:bg-white focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all duration-150 max-w-[260px] truncate"
                >
                  {asignaturas.map((a) => (
                    <option key={a.id} value={slugify(a.nombre)}>
                      {a.nombre}
                    </option>
                  ))}
                </select>
                <span className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-gray-400">
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                  </svg>
                </span>
              </div>
            )}

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
