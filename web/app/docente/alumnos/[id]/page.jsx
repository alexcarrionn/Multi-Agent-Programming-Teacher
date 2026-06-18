"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import axios from "axios";
import Image from "next/image";
import { sileo } from "sileo";
import { ArrowLeft } from "lucide-react";
import { useAuth } from "@/app/context/AuthContext";
import { useTranslation } from "react-i18next";
import "@/lib/i18n";
import { Button } from "@/app/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/app/components/ui/table";

export default function AlumnoDetallePage() {
  const { id } = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const asignaturaId = searchParams.get("asignatura_id");
  const { user, logout } = useAuth();
  const { t } = useTranslation();

  const [alumno, setAlumno] = useState(null);
  const [progreso, setProgreso] = useState([]);
  const [interacciones, setInteracciones] = useState([]);
  const [loading, setLoading] = useState(true);

  const getErrorMessage = (err) => {
    if (axios.isAxiosError(err)) {
      return err.response?.data?.detail || err.response?.data?.message || err.message || t("error_network");
    }
    return t("error_generic");
  };

  useEffect(() => {
    if (!id) return;
    const load = async () => {
      try {
        const queryAsignatura = asignaturaId ? `?asignatura_id=${asignaturaId}` : "";
        const progresoUrl = `/backend/api/docente/alumnos/${id}/progreso${queryAsignatura}`;
        const interaccionesUrl = `/backend/api/docente/alumnos/${id}/interacciones${queryAsignatura}`;
        const [alumnoRes, progresoRes, interaccionesRes] = await Promise.all([
          axios.get(`/backend/api/docente/alumnos/${id}`, { withCredentials: true }),
          axios.get(progresoUrl, { withCredentials: true }),
          axios.get(interaccionesUrl, { withCredentials: true }),
        ]);
        setAlumno(alumnoRes.data);
        setProgreso(progresoRes.data.progreso || []);
        setInteracciones(interaccionesRes.data.interacciones || []);
      } catch (err) {
        if (err.response?.status === 403) {
          sileo.error({
            title: t("error"),
            description: t("docente_alumno_not_accessible"),
          });
          router.push("/docente");
          return;
        }
        sileo.error({ title: t("error"), description: getErrorMessage(err) });
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id, asignaturaId, router, t]);

  const handleLogout = async () => {
    await logout();
    router.push("/auth/docente/login");
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
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.back()}
          className="mb-4"
        >
          <ArrowLeft /> {t("docente_back")}
        </Button>

        {loading ? (
          <p className="text-sm text-gray-500">{t("loading")}</p>
        ) : alumno ? (
          <>
            <div className="bg-white p-6 rounded-xl border border-gray-200 mb-6">
              <h1 className="text-2xl font-bold text-gray-900 mb-1">{alumno.nombre}</h1>
              <p className="text-sm text-gray-500">{alumno.email}</p>
              <p className="text-sm text-gray-500 mt-1">
                {t("docente_alumno_nivel")}: <span className="font-medium text-gray-700">{alumno.nivel || "—"}</span>
              </p>
            </div>

            <div className="mb-8">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">
                {t("docente_alumno_progreso_title")}
              </h2>
              <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                {progreso.length === 0 ? (
                  <p className="p-6 text-sm text-gray-500">{t("docente_alumno_progreso_empty")}</p>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>{t("docente_alumno_progreso_col_enunciado")}</TableHead>
                        <TableHead className="w-24">{t("docente_alumno_progreso_col_puntuacion")}</TableHead>
                        <TableHead className="w-40">{t("docente_alumno_progreso_col_ambito")}</TableHead>
                        <TableHead className="w-44">{t("docente_alumno_progreso_col_fecha")}</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {progreso.map((p, idx) => (
                        <TableRow key={idx}>
                          <TableCell className="text-sm text-gray-700 whitespace-pre-wrap">
                            {p.enunciado || "—"}
                          </TableCell>
                          <TableCell className="font-medium">{p.puntuacion || "—"}</TableCell>
                          <TableCell className="text-gray-600">{p.ambito || "—"}</TableCell>
                          <TableCell className="text-gray-600 text-sm">{formatFecha(p.fecha)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-lg font-semibold text-gray-900">
                  {t("docente_alumno_interacciones_title")}
                </h2>
                {interacciones.length > 0 && (
                  <button
                    type="button"
                    onClick={() =>
                      router.push(
                        `/docente/interacciones?alumno_id=${id}${asignaturaId ? `&asignatura_id=${asignaturaId}` : ""}`
                      )
                    }
                    className="btn-codi-animated w-auto px-5 text-sm"
                  >
                    {t("docente_alumno_interacciones_view_all")}
                  </button>
                )}
              </div>
              {interacciones.length === 0 ? (
                <div className="bg-white rounded-xl border border-gray-200 p-6">
                  <p className="text-sm text-gray-500">{t("docente_alumno_interacciones_empty")}</p>
                </div>
              ) : (
                <div className="flex flex-col gap-3">
                  {interacciones.slice(0, 5).map((i, idx) => (
                    <div
                      key={idx}
                      className="bg-white rounded-xl border border-gray-200 p-4"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-medium text-blue-700 bg-blue-50 px-2 py-1 rounded">
                          {i.tipo_interaccion || "—"}
                        </span>
                        <span className="text-xs text-gray-500">{formatFecha(i.fecha)}</span>
                      </div>
                      <div className="mb-2">
                        <p className="text-xs text-gray-500 mb-1">
                          {t("docente_alumno_interacciones_user")}
                        </p>
                        <p className="text-sm text-gray-800 whitespace-pre-wrap">{i.mensaje_usuario}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 mb-1">
                          {t("docente_alumno_interacciones_agent")}
                        </p>
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">{i.respuesta_agente}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        ) : null}
      </section>
    </main>
  );
}
