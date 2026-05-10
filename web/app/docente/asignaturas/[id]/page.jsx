"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import axios from "axios";
import Image from "next/image";
import { sileo } from "sileo";
import { ArrowLeft, Upload } from "lucide-react";
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

export default function AsignaturaPage() {
  const { id } = useParams();
  const router = useRouter();
  const { user, logout } = useAuth();
  const { t } = useTranslation();

  const [asignatura, setAsignatura] = useState(null);
  const [alumnos, setAlumnos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  const getErrorMessage = (err) => {
    if (axios.isAxiosError(err)) {
      return err.response?.data?.detail || err.response?.data?.message || err.message || t("error_network");
    }
    return t("error_generic");
  };

  const fetchAlumnos = useCallback(async () => {
    try {
      const { data } = await axios.get(
        `/backend/api/docente/asignaturas/${id}/alumnos`,
        { withCredentials: true }
      );
      setAlumnos(data.alumnos || []);
    } catch (err) {
      sileo.error({ title: t("error"), description: getErrorMessage(err) });
    }
  }, [id, t]);

  useEffect(() => {
    if (!id) return;
    const load = async () => {
      try {
        const [asignaturaRes, alumnosRes] = await Promise.all([
          axios.get(`/backend/api/docente/asignaturas/${id}`, { withCredentials: true }),
          axios.get(`/backend/api/docente/asignaturas/${id}/alumnos`, { withCredentials: true }),
        ]);
        setAsignatura(asignaturaRes.data);
        setAlumnos(alumnosRes.data.alumnos || []);
      } catch (err) {
        if (err.response?.status === 403) {
          sileo.error({
            title: t("error"),
            description: t("docente_subject_not_accessible"),
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
  }, [id, router, t]);

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await axios.post(
        `/backend/api/docente/asignaturas/${id}/import-alumnos`,
        formData,
        { withCredentials: true, headers: { "Content-Type": "multipart/form-data" } }
      );
      sileo.success({
        title: t("docente_import_success_title"),
        description: t("docente_import_success_msg", { insertados: data.insertados }),
      });
      await fetchAlumnos();
    } catch (err) {
      sileo.error({ title: t("error"), description: getErrorMessage(err) });
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteAlumno = async (alumno) => {
    if (!confirm(t("docente_alumno_delete_confirm", { nombre: alumno.nombre }))) return;
    try {
      await axios.delete(
        `/backend/api/docente/asignaturas/${id}/alumnos/${alumno.id}`,
        { withCredentials: true }
      );
      sileo.success({
        title: t("docente_alumno_delete_success_title"),
        description: t("docente_alumno_delete_success_msg"),
      });
      await fetchAlumnos();
    } catch (err) {
      sileo.error({ title: t("error"), description: getErrorMessage(err) });
    }
  };

  const handleLogout = async () => {
    await logout();
    router.push("/auth/docente/login");
  };

  return (
    <main className="min-h-screen bg-gray-100">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
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

      <section className="max-w-6xl mx-auto px-6 py-8">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push("/docente")}
          className="mb-4"
        >
          <ArrowLeft /> {t("docente_back")}
        </Button>

        {loading ? (
          <p className="text-sm text-gray-500">{t("loading")}</p>
        ) : asignatura ? (
          <>
            <div className="bg-white p-6 rounded-xl border border-gray-200 mb-6">
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900 mb-1">{asignatura.nombre}</h1>
                  <p className="text-sm text-gray-500">
                    {t("docente_subject_code")}: <span className="font-mono">{asignatura.codigo}</span>
                  </p>
                </div>
                <Button onClick={handleUploadClick} disabled={uploading}>
                  <Upload /> {uploading ? t("loading") : t("docente_upload_excel_button")}
                </Button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".xlsx,.xls"
                  className="hidden"
                  onChange={handleFileChange}
                />
              </div>
            </div>

            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-3">{t("docente_alumnos")}</h2>
              <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                {alumnos.length === 0 ? (
                  <p className="p-6 text-sm text-gray-500">{t("docente_alumnos_empty")}</p>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>{t("docente_alumnos_col_nombre")}</TableHead>
                        <TableHead>{t("docente_alumnos_col_email")}</TableHead>
                        <TableHead>{t("docente_alumnos_col_nivel")}</TableHead>
                        <TableHead className="w-12"></TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {alumnos.map((a) => (
                        <TableRow
                          key={a.id}
                          className="cursor-pointer"
                          onClick={() => router.push(`/docente/alumnos/${a.id}`)}
                        >
                          <TableCell className="font-medium">{a.nombre}</TableCell>
                          <TableCell className="text-gray-600">{a.email}</TableCell>
                          <TableCell className="text-gray-600">{a.nivel || "—"}</TableCell>
                          <TableCell>
                            <Button
                              variant="ghost"
                              size="icon-sm"
                              aria-label={t("docente_alumnos_delete")}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteAlumno(a);
                              }}
                            >
                              <Image
                                src="/imagenes_eliminar/eliminar-usuario.png"
                                alt=""
                                width={18}
                                height={18}
                              />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </div>
            </div>
          </>
        ) : null}
      </section>
    </main>
  );
}
