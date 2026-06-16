"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import axios from "axios";
import Image from "next/image";
import { sileo } from "sileo";
import { ArrowLeft, FileText, Trash2, Upload } from "lucide-react";
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/app/components/ui/dialog";

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

  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [newCorreo, setNewCorreo] = useState("");
  const [creating, setCreating] = useState(false);

  const [documentos, setDocumentos] = useState([]);
  const [docDialogOpen, setDocDialogOpen] = useState(false);
  const [docTipo, setDocTipo] = useState("teoria");
  const [docFiles, setDocFiles] = useState([]);
  const [uploadingDocs, setUploadingDocs] = useState(false);

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

  const fetchDocumentos = useCallback(async () => {
    try {
      const { data } = await axios.get(
        `/backend/api/docente/asignaturas/${id}/documentos`,
        { withCredentials: true }
      );
      setDocumentos(data.documentos || []);
    } catch (err) {
      sileo.error({ title: t("error"), description: getErrorMessage(err) });
    }
  }, [id, t]);

  useEffect(() => {
    if (!id) return;
    const load = async () => {
      try {
        const [asignaturaRes, alumnosRes, documentosRes] = await Promise.all([
          axios.get(`/backend/api/docente/asignaturas/${id}`, { withCredentials: true }),
          axios.get(`/backend/api/docente/asignaturas/${id}/alumnos`, { withCredentials: true }),
          axios.get(`/backend/api/docente/asignaturas/${id}/documentos`, { withCredentials: true }),
        ]);
        setAsignatura(asignaturaRes.data);
        setAlumnos(alumnosRes.data.alumnos || []);
        setDocumentos(documentosRes.data.documentos || []);
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

  const resetAddDialog = () => {
    setNewCorreo("");
  };

  const handleCrearAlumnoAutorizado = async (e) => {
    e.preventDefault();
    const correo = newCorreo.trim();
    if (!correo) return;
    setCreating(true);
    try {
      await axios.post(
        `/backend/api/docente/asignaturas/${id}/alumnos-autorizados`,
        { correo },
        { withCredentials: true }
      );
      sileo.success({
        title: t("docente_add_student_success_title"),
        description: t("docente_add_student_success_msg", { correo }),
      });
      setAddDialogOpen(false);
      resetAddDialog();
      await fetchAlumnos();
    } catch (err) {
      sileo.error({ title: t("error"), description: getErrorMessage(err) });
    } finally {
      setCreating(false);
    }
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

  const resetDocDialog = () => {
    setDocTipo("teoria");
    setDocFiles([]);
  };

  const handleSubmitDocs = async (e) => {
    e.preventDefault();
    if (docFiles.length === 0) return;
    setUploadingDocs(true);
    try {
      const formData = new FormData();
      formData.append("tipo", docTipo);
      docFiles.forEach((f) => formData.append("files", f));
      const { data } = await axios.post(
        `/backend/api/docente/asignaturas/${id}/documentos`,
        formData,
        { withCredentials: true, headers: { "Content-Type": "multipart/form-data" } }
      );
      sileo.success({
        title: t("docente_doc_upload_success_title"),
        description: t("docente_doc_upload_success_msg", {
          insertados: data.insertados,
          fallos: data.fallos.length,
        }),
      });
      setDocDialogOpen(false);
      resetDocDialog();
      await fetchDocumentos();
    } catch (err) {
      sileo.error({ title: t("error"), description: getErrorMessage(err) });
    } finally {
      setUploadingDocs(false);
    }
  };

  const handleDeleteDocumento = async (doc) => {
    if (!confirm(t("docente_doc_delete_confirm", { nombre: doc.nombre }))) return;
    try {
      await axios.delete(
        `/backend/api/docente/asignaturas/${id}/documentos`,
        {
          withCredentials: true,
          params: { tipo: doc.tipo, nombre: doc.nombre },
        }
      );
      sileo.success({
        title: t("docente_doc_delete_success_title"),
        description: t("docente_doc_delete_success_msg"),
      });
      await fetchDocumentos();
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
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <h1 className="text-2xl font-bold text-gray-900">{asignatura.nombre}</h1>
                    {asignatura.tipo && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                        {t(`tipo_${asignatura.tipo}`)}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500">
                    {t("docente_subject_code")}: <span className="font-mono">{asignatura.codigo}</span>
                  </p>
                </div>

                <div className="flex flex-col sm:flex-row gap-2">
                  <Button
                    variant="outline"
                    onClick={() => setAddDialogOpen(true)}
                    disabled={uploading || creating}
                  >
                    {t("docente_upload_student")}
                  </Button>
                  <Button onClick={handleUploadClick} disabled={uploading}>
                    <Upload /> {uploading ? t("loading") : t("docente_upload_excel_button")}
                  </Button>
                  <button
                    type="button"
                    onClick={() => setDocDialogOpen(true)}
                    disabled={uploadingDocs}
                    className="btn-codi-animated rounded-md px-3.5 text-sm whitespace-nowrap inline-flex items-center justify-center gap-1.5 disabled:opacity-60 disabled:cursor-not-allowed"
                    style={{ width: "auto", height: "2.25rem", fontSize: "0.875rem" }}
                  >
                    <FileText className="w-4 h-4" />
                    {t("docente_add_doc_button")}
                  </button>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".xlsx,.xls"
                  className="hidden"
                  onChange={handleFileChange}
                />
              </div>
            </div>

            <div className="mb-8">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">{t("docente_doc_section_title")}</h2>
              <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                {documentos.length === 0 ? (
                  <p className="p-6 text-sm text-gray-500">{t("docente_doc_empty")}</p>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>{t("docente_doc_col_nombre")}</TableHead>
                        <TableHead className="w-32">{t("docente_doc_col_tipo")}</TableHead>
                        <TableHead className="w-12"></TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {documentos.map((d) => (
                        <TableRow key={`${d.tipo}/${d.nombre}`}>
                          <TableCell className="font-medium">{d.nombre}</TableCell>
                          <TableCell className="text-gray-600">
                            {d.tipo === "teoria" ? t("docente_doc_tipo_teoria") : t("docente_doc_tipo_practicas")}
                          </TableCell>
                          <TableCell>
                            <Button
                              variant="ghost"
                              size="icon-sm"
                              aria-label={t("docente_doc_delete")}
                              onClick={() => handleDeleteDocumento(d)}
                            >
                              <Trash2 className="w-4 h-4 text-red-600" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
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
                          onClick={() => router.push(`/docente/alumnos/${a.id}?asignatura_id=${id}`)}
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

      <Dialog
        open={docDialogOpen}
        onOpenChange={(open) => {
          setDocDialogOpen(open);
          if (!open) resetDocDialog();
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("docente_doc_dialog_title")}</DialogTitle>
            <DialogDescription>{t("docente_doc_dialog_desc")}</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmitDocs} className="flex flex-col gap-3">
            <label className="flex flex-col gap-1 text-sm">
              <span className="font-medium">{t("docente_doc_tipo_label")}</span>
              <select
                value={docTipo}
                onChange={(e) => setDocTipo(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="teoria">{t("docente_doc_tipo_teoria")}</option>
                <option value="practicas">{t("docente_doc_tipo_practicas")}</option>
              </select>
            </label>
            <div className="flex flex-col gap-2 text-sm">
              <span className="font-medium">{t("docente_doc_files_label")}</span>
              <input
                id="doc-files-input"
                type="file"
                multiple
                accept=".pdf,.txt,.docx,.md"
                onChange={(e) => {
                  const nuevos = Array.from(e.target.files || []);
                  setDocFiles((prev) => {
                    const existentes = new Set(prev.map((f) => f.name));
                    return [...prev, ...nuevos.filter((f) => !existentes.has(f.name))];
                  });
                  e.target.value = "";
                }}
                className="hidden"
              />
              <label
                htmlFor="doc-files-input"
                className="cursor-pointer border border-dashed border-gray-300 rounded-md px-4 py-6 text-center text-sm text-gray-500 hover:border-blue-400 hover:bg-blue-50/40 transition"
              >
                <Upload className="inline-block w-4 h-4 mr-2" />
                {t("docente_doc_files_pick")}
                <span className="block text-xs text-gray-400 mt-1">.pdf · .txt · .docx · .md</span>
              </label>
              {docFiles.length > 0 && (
                <ul className="flex flex-col gap-1 mt-1 max-h-32 overflow-y-auto">
                  {docFiles.map((f, idx) => (
                    <li
                      key={`${f.name}-${idx}`}
                      className="flex items-center justify-between bg-gray-50 border border-gray-200 rounded-md px-3 py-1.5 text-xs"
                    >
                      <span className="truncate text-gray-700">{f.name}</span>
                      <button
                        type="button"
                        onClick={() => setDocFiles((prev) => prev.filter((_, i) => i !== idx))}
                        className="ml-2 text-gray-400 hover:text-red-600"
                        aria-label={t("docente_doc_files_remove")}
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setDocDialogOpen(false)}
                disabled={uploadingDocs}
              >
                {t("cancel")}
              </Button>
              <Button type="submit" disabled={uploadingDocs || docFiles.length === 0}>
                {uploadingDocs ? t("loading") : t("docente_doc_submit")}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog
        open={addDialogOpen}
        onOpenChange={(open) => {
          setAddDialogOpen(open);
          if (!open) resetAddDialog();
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("docente_add_student_dialog_title")}</DialogTitle>
            <DialogDescription>{t("docente_add_student_dialog_desc")}</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCrearAlumnoAutorizado} className="flex flex-col gap-3">
            <label className="flex flex-col gap-1 text-sm">
              <span className="font-medium">{t("docente_add_student_email_label")}</span>
              <input
                type="email"
                value={newCorreo}
                onChange={(e) => setNewCorreo(e.target.value)}
                required
                autoFocus
                className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </label>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setAddDialogOpen(false)}
                disabled={creating}
              >
                {t("cancel")}
              </Button>
              <Button type="submit" disabled={creating}>
                {creating ? t("loading") : t("docente_add_student_submit")}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </main>
  );
}
