"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import axios from "axios";
import Image from "next/image";
import { sileo } from "sileo";
import { ArrowLeft, Download } from "lucide-react";
import { useAuth } from "@/app/context/AuthContext";
import { useTranslation } from "react-i18next";
import "@/lib/i18n";
import { Button } from "@/app/components/ui/button";

export default function InteraccionesDocentePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, logout } = useAuth();
  const { t } = useTranslation();

  const [asignaturas, setAsignaturas] = useState([]);
  // Estado inicial desde la URL: permite enlazar desde la ficha del alumno
  // (/docente/interacciones?asignatura_id=&alumno_id=) ya filtrado.
  const [filtro, setFiltro] = useState(() => searchParams.get("asignatura_id") || ""); // asignatura ("" = todas)
  const [filtroAlumno, setFiltroAlumno] = useState(() => searchParams.get("alumno_id") || ""); // alumno ("" = todos)
  const [orden, setOrden] = useState("reciente"); // "reciente" | "antigua"
  const [interacciones, setInteracciones] = useState([]);
  const [loading, setLoading] = useState(true);

  // Lista de alumnos para el desplegable, derivada de las interacciones cargadas
  // (unicos por alumno_id). Asi refleja solo quien realmente tiene interacciones.
  const alumnos = Array.from(
    new Map(interacciones.map((i) => [i.alumno_id, { id: i.alumno_id, nombre: i.alumno_nombre, email: i.alumno_email }])).values()
  ).sort((a, b) => (a.nombre || "").localeCompare(b.nombre || ""));

  // Filtros en cliente: alumno y ordenacion por fecha.
  const interaccionesFiltradas = interacciones
    .filter((i) => !filtroAlumno || String(i.alumno_id) === filtroAlumno)
    .slice()
    .sort((a, b) => {
      const ta = a.fecha ? new Date(a.fecha).getTime() : 0;
      const tb = b.fecha ? new Date(b.fecha).getTime() : 0;
      return orden === "antigua" ? ta - tb : tb - ta;
    });

  const getErrorMessage = (err) => {
    if (axios.isAxiosError(err)) {
      return err.response?.data?.detail || err.response?.data?.message || err.message || t("error_network");
    }
    return t("error_generic");
  };

  // Cargamos las asignaturas una vez para el desplegable de filtro.
  useEffect(() => {
    const loadAsignaturas = async () => {
      try {
        const { data } = await axios.get("/backend/api/docente/asignaturas", { withCredentials: true });
        setAsignaturas(data.asignaturas || []);
      } catch (err) {
        sileo.error({ title: t("error"), description: getErrorMessage(err) });
      }
    };
    loadAsignaturas();
  }, [t]);

  // Recargamos las interacciones cada vez que cambia el filtro de asignatura (backend).
  useEffect(() => {
    const loadInteracciones = async () => {
      setLoading(true);
      try {
        const query = filtro ? `?asignatura_id=${filtro}` : "";
        const { data } = await axios.get(`/backend/api/docente/interacciones${query}`, { withCredentials: true });
        setInteracciones(data.interacciones || []);
      } catch (err) {
        sileo.error({ title: t("error"), description: getErrorMessage(err) });
      } finally {
        setLoading(false);
      }
    };
    loadInteracciones();
  }, [filtro, t]);

  const handleLogout = async () => {
    await logout();
    router.push("/auth/docente/login");
  };

  // Descarga el .xlsx respetando los filtros activos (asignatura + alumno).
  // Usamos un <a> temporal: al ser GET con cookie de sesion same-origin, el
  // navegador descarga el fichero (Content-Disposition) sin navegar fuera.
  const exportar = () => {
    const params = new URLSearchParams();
    if (filtro) params.set("asignatura_id", filtro);
    if (filtroAlumno) params.set("alumno_id", filtroAlumno);
    const qs = params.toString();
    const a = document.createElement("a");
    a.href = `/backend/api/docente/interacciones/export${qs ? `?${qs}` : ""}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  const formatFecha = (iso) => {
    if (!iso) return "—";
    try {
      return new Date(iso).toLocaleString();
    } catch {
      return iso;
    }
  };

  return (
    <main className="min-h-screen bg-gray-100">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Image src="/logo.svg" alt="Logo de Codi" width={32} height={32} priority />
            <span className="font-semibold text-gray-900">Codi · {t("docente_panel")}</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600 hidden sm:block">{user?.nombre}</span>
            <Button
              variant="outline"
              size="sm"
              onClick={handleLogout}
              className="hover:bg-red-50 hover:text-red-700 hover:border-red-200"
            >
              {t("header_logout")}
            </Button>
          </div>
        </div>
      </header>

      <section className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <Button variant="ghost" size="sm" onClick={() => router.push("/docente")} className="mb-4">
          <ArrowLeft /> {t("docente_back")}
        </Button>

        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{t("docente_interactions_title")}</h1>
            <p className="text-sm text-gray-500 mt-1">{t("docente_interactions_subtitle")}</p>
          </div>
          <button
            type="button"
            onClick={exportar}
            disabled={loading || interaccionesFiltradas.length === 0}
            className="btn-codi-animated w-full sm:w-auto px-5 inline-flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download className="h-4 w-4" /> {t("docente_interactions_export")}
          </button>
        </div>

        {/* Panel de filtros */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-gray-700" htmlFor="filtro-asignatura">
                {t("docente_interactions_filter_label")}
              </label>
              <select
                id="filtro-asignatura"
                className="w-full p-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm bg-white"
                value={filtro}
                onChange={(e) => { setFiltro(e.target.value); setFiltroAlumno(""); }}
              >
                <option value="">{t("docente_interactions_filter_all")}</option>
                {asignaturas.map((a) => (
                  <option key={a.id} value={a.id}>{a.nombre}</option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-gray-700" htmlFor="filtro-alumno">
                {t("docente_interactions_filter_student_label")}
              </label>
              <select
                id="filtro-alumno"
                className="w-full p-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm bg-white"
                value={filtroAlumno}
                onChange={(e) => setFiltroAlumno(e.target.value)}
              >
                <option value="">{t("docente_interactions_filter_student_all")}</option>
                {alumnos.map((a) => (
                  <option key={a.id} value={a.id}>{a.nombre}</option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-gray-700" htmlFor="orden">
                {t("docente_interactions_sort_label")}
              </label>
              <select
                id="orden"
                className="w-full p-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm bg-white"
                value={orden}
                onChange={(e) => setOrden(e.target.value)}
              >
                <option value="reciente">{t("docente_interactions_sort_recent")}</option>
                <option value="antigua">{t("docente_interactions_sort_oldest")}</option>
              </select>
            </div>
          </div>
        </div>

        {loading ? (
          <p className="text-sm text-gray-500">{t("loading")}</p>
        ) : interaccionesFiltradas.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <p className="text-sm text-gray-500">{t("docente_interactions_empty")}</p>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {interaccionesFiltradas.map((i, idx) => (
              <div key={idx} className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                  <div className="min-w-0">
                    <span className="text-sm font-semibold text-gray-900 truncate block">
                      {i.alumno_nombre}
                    </span>
                    <span className="text-xs text-gray-500 truncate block">{i.alumno_email}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-purple-700 bg-purple-50 px-2 py-1 rounded">
                      {i.asignatura}
                    </span>
                    {i.tipo_interaccion && (
                      <span className="text-xs font-medium text-blue-700 bg-blue-50 px-2 py-1 rounded">
                        {i.tipo_interaccion}
                      </span>
                    )}
                    <span className="text-xs text-gray-500">{formatFecha(i.fecha)}</span>
                  </div>
                </div>
                <div className="mb-2">
                  <p className="text-xs text-gray-500 mb-1">{t("docente_alumno_interacciones_user")}</p>
                  <p className="text-sm text-gray-800 whitespace-pre-wrap">{i.mensaje_usuario}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 mb-1">{t("docente_alumno_interacciones_agent")}</p>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">{i.respuesta_agente}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
