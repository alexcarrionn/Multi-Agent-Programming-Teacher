"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import Image from "next/image";
import { sileo } from "sileo";
import { Plus, LogIn, Copy, Check, MessageSquare } from "lucide-react";
import { useAuth } from "@/app/context/AuthContext";
import { useTranslation } from "react-i18next";
import "@/lib/i18n";
import { Button } from "@/app/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/app/components/ui/dialog";

export default function DocenteDashboard() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const { t } = useTranslation();

  const [asignaturas, setAsignaturas] = useState([]);
  const [loading, setLoading] = useState(true);

  const [createOpen, setCreateOpen] = useState(false);
  const [joinOpen, setJoinOpen] = useState(false);
  const [createInput, setCreateInput] = useState({ nombre: "", codigo: "" , tipo: "programacion"});
  const [joinInput, setJoinInput] = useState({ codigo: "" });
  const [submitting, setSubmitting] = useState(false);
  const [copiedId, setCopiedId] = useState(null);

  const getErrorMessage = (err) => {
    if (axios.isAxiosError(err)) {
      return err.response?.data?.detail || err.response?.data?.message || err.message || t("error_network");
    }
    return t("error_generic");
  };

  const handleError = (err) => {
    sileo.error({ title: t("error"), description: getErrorMessage(err) });
    if (err) console.error("Error:", err);
  };

  const fetchAsignaturas = async () => {
    try {
      const { data } = await axios.get("/backend/api/docente/asignaturas", { withCredentials: true });
      setAsignaturas(data.asignaturas || []);
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAsignaturas();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await axios.post(
        "/backend/api/docente/asignaturas",
        { nombre: createInput.nombre, codigo: createInput.codigo, tipo: createInput.tipo },
        { withCredentials: true }
      );
      sileo.success({ title: t("docente_create_success_title"), description: t("docente_create_success_msg") });
      setCreateInput({ nombre: "", codigo: "", tipo: "programacion" });
      setCreateOpen(false);
      await fetchAsignaturas();
    } catch (err) {
      handleError(err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleJoin = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await axios.post(
        "/backend/api/docente/unirse-asignatura",
        { codigo: joinInput.codigo },
        { withCredentials: true }
      );
      sileo.success({ title: t("docente_join_success_title"), description: t("docente_join_success_msg") });
      setJoinInput({ codigo: "" });
      setJoinOpen(false);
      await fetchAsignaturas();
    } catch (err) {
      handleError(err);
    } finally {
      setSubmitting(false);
    }
  };

  const copyCode = async (id, codigo) => {
    try {
      await navigator.clipboard.writeText(codigo);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch {
      sileo.error({ title: t("error"), description: t("error_generic") });
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
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <h1 className="text-2xl font-bold text-gray-900">{t("docente_my_subjects")}</h1>
           <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
            <Button variant="outline" className="w-full sm:w-auto" onClick={() => router.push("/docente/interacciones")}>
              <MessageSquare /> {t("docente_interactions_view")}
            </Button>
            <Button variant="outline" className="w-full sm:w-auto" onClick={() => setJoinOpen(true)}>
              <LogIn /> {t("docente_join_subject")}
            </Button>
            <Button className="btn-codi-animated w-full sm:w-auto" onClick={() => setCreateOpen(true)}>
              <Plus /> {t("docente_create_subject")}
            </Button>
          </div>
        </div>

        {loading ? (
          <p className="text-sm text-gray-500">{t("loading")}</p>
        ) : asignaturas.length === 0 ? (
          <div className="bg-white border border-dashed border-gray-300 rounded-xl p-10 text-center">
            <p className="text-gray-600 mb-4">{t("docente_no_subjects")}</p>
            <div className="flex justify-center gap-2">
              <Button variant="outline" onClick={() => setJoinOpen(true)}>
                <LogIn /> {t("docente_join_subject")}
              </Button>
              <Button onClick={() => setCreateOpen(true)}>
                <Plus /> {t("docente_create_subject")}
              </Button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {asignaturas.map((a) => (
              <div
                key={a.id}
                role="button"
                tabIndex={0}
                onClick={() => router.push(`/docente/asignaturas/${a.id}`)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    router.push(`/docente/asignaturas/${a.id}`);
                  }
                }}
                className="text-left bg-white p-5 rounded-xl border border-gray-200 hover:border-blue-400 hover:shadow-md transition-all cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <div className="flex items-start justify-between gap-2 mb-1">
                  <h2 className="font-semibold text-gray-900">{a.nombre}</h2>
                  {a.tipo && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-blue-100 text-blue-800 whitespace-nowrap">
                      {t(`tipo_${a.tipo}`)}
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-500 mb-4">{t("docente_subject_code")}: {a.codigo}</p>
                <div className="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2">
                  <div className="min-w-0">
                    <p className="text-[11px] uppercase tracking-wide text-gray-500">{t("docente_invitation_code")}</p>
                    <p className="font-mono text-sm text-gray-900 truncate">{a.codigo_invitacion}</p>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    onClick={(e) => { e.stopPropagation(); copyCode(a.id, a.codigo_invitacion); }}
                    aria-label={t("docente_copy_code")}
                  >
                    {copiedId === a.id ? <Check /> : <Copy />}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("docente_create_subject")}</DialogTitle>
            <DialogDescription>{t("docente_create_subject_desc")}</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreate} className="flex flex-col gap-3">
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-gray-700" htmlFor="create-nombre">
                {t("docente_subject_name")}
              </label>
              <input
                id="create-nombre"
                className="w-full p-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                value={createInput.nombre}
                onChange={(e) => setCreateInput({ ...createInput, nombre: e.target.value })}
                required
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-gray-700" htmlFor="create-codigo">
                {t("docente_subject_code")}
              </label>
              <input
                id="create-codigo"
                className="w-full p-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                value={createInput.codigo}
                onChange={(e) => setCreateInput({ ...createInput, codigo: e.target.value })}
                required
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-gray-700" htmlFor="create-tipo">
                {t("docente_subject_type_label")}
              </label>
              <select
                id="create-tipo"
                className="w-full p-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm bg-white"
                value={createInput.tipo}
                onChange={(e) => setCreateInput({ ...createInput, tipo: e.target.value })}
              >
                <option value="programacion">{t("tipo_programacion")}</option>
                <option value="formacion_basica">{t("tipo_formacion_basica")}</option>
              </select>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setCreateOpen(false)} disabled={submitting}>
                {t("cancel")}
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? t("loading") : t("docente_create_subject")}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={joinOpen} onOpenChange={setJoinOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("docente_join_subject")}</DialogTitle>
            <DialogDescription>{t("docente_join_subject_desc")}</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleJoin} className="flex flex-col gap-3">
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-gray-700" htmlFor="join-codigo">
                {t("docente_invitation_code_input")}
              </label>
              <input
                id="join-codigo"
                className="w-full p-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-mono"
                value={joinInput.codigo}
                onChange={(e) => setJoinInput({ codigo: e.target.value.trim() })}
                required
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setJoinOpen(false)} disabled={submitting}>
                {t("cancel")}
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? t("loading") : t("docente_join_subject")}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </main>
  );
}
