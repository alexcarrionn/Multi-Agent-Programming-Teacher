"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/app/components/ui/button";
import axios from "axios";
import Image from "next/image";
import { sileo } from "sileo";
import { MailCheck } from "lucide-react";
import { useTranslation } from "react-i18next";
import "@/lib/i18n";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [enviado, setEnviado] = useState(false);
  const [loading, setLoading] = useState(false);
  const { t } = useTranslation();

  const getErrorMessage = (err) => {
    if (!err) return t("error_generic");
    if (typeof err === "string") return err;
    if (axios.isAxiosError(err)) {
      return (
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        t("error_network")
      );
    }
    return t("error_generic");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post("/backend/api/forgot-password", { email });
      setEnviado(true);
    } catch (err) {
      sileo.error({ title: t("error"), description: getErrorMessage(err) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center p-6 bg-gray-100">
      <div className="w-full max-w-md bg-white p-8 rounded-2xl shadow-lg border border-gray-100">
        <div className="flex flex-col items-center mb-8">
          <Image src="/logo.svg" alt="Logo de Codi" width={48} height={48} priority className="mb-4" />
          <h1 className="text-3xl font-bold text-gray-900">{t("forgot_title")}</h1>
          <p className="text-sm text-gray-500 mt-2 text-center">{t("forgot_subtitle")}</p>
        </div>

        {enviado ? (
          <div className="flex flex-col items-center gap-4 py-4">
            <MailCheck size={48} className="text-blue-500" />
            <p className="text-gray-700 text-center font-medium">{t("forgot_sent_title")}</p>
            <p className="text-sm text-gray-500 text-center">
              {t("forgot_sent_msg", { email })}
            </p>
            <Button asChild variant="outline" className="w-full mt-4 py-2.5 rounded-lg">
              <Link href="/auth/login">{t("back_to_login")}</Link>
            </Button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-gray-700" htmlFor="email">
                {t("forgot_email")}
              </label>
              <input
                id="email"
                type="email"
                name="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                placeholder="tucorreo@um.es"
                required
              />
            </div>

            <div className="flex flex-col gap-3 mt-2">
              <button
                type="submit"
                disabled={loading}
                className="btn-codi-animated mt-2 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {loading ? t("forgot_sending") : t("forgot_submit")}
              </button>
              <Button asChild variant="outline" type="button" className="w-full py-2.5 rounded-lg">
                <Link href="/auth/login">{t("back_to_login")}</Link>
              </Button>
            </div>
          </form>
        )}
      </div>
    </main>
  );
}
