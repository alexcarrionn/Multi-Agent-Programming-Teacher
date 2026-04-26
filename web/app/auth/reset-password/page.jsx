"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/app/components/ui/button";
import axios from "axios";
import Image from "next/image";
import { sileo } from "sileo";
import { Eye, EyeOff } from "lucide-react";
import { useTranslation } from "react-i18next";
import "@/lib/i18n";

export default function ResetPassword() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const { t } = useTranslation();

  const [input, setInput] = useState({ password: "", confirmPassword: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);

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

  const handleChange = (e) => {
    const { name, value } = e.target;
    setInput((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (input.password !== input.confirmPassword) {
      sileo.error({ title: t("error"), description: t("passwords_dont_match") });
      return;
    }

    if (input.password.length < 8) {
      sileo.error({ title: t("error"), description: t("password_min_chars") });
      return;
    }

    setLoading(true);
    try {
      await axios.post("/backend/api/reset-password", { token, new_password: input.password });
      sileo.success({ title: t("reset_success_title"), description: t("reset_success_msg") });
      setTimeout(() => router.push("/auth/login"), 1500);
    } catch (err) {
      sileo.error({ title: t("error"), description: getErrorMessage(err) });
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <main className="relative flex min-h-screen flex-col items-center justify-center p-6 bg-gray-100">
        <div className="w-full max-w-md bg-white p-8 rounded-2xl shadow-lg border border-gray-100 flex flex-col items-center gap-4">
          <Image src="/logo.svg" alt="Logo de Codi" width={48} height={48} priority />
          <h1 className="text-xl font-bold text-gray-900">{t("reset_invalid_title")}</h1>
          <p className="text-sm text-gray-500 text-center">{t("reset_invalid_msg")}</p>
          <Button asChild variant="outline" className="w-full py-2.5 rounded-lg">
            <Link href="/auth/forgot-password">{t("reset_request_link")}</Link>
          </Button>
        </div>
      </main>
    );
  }

  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center p-6 bg-gray-100">
      <div className="w-full max-w-md bg-white p-8 rounded-2xl shadow-lg border border-gray-100">
        <div className="flex flex-col items-center mb-8">
          <Image src="/logo.svg" alt="Logo de Codi" width={48} height={48} priority className="mb-4" />
          <h1 className="text-3xl font-bold text-gray-900">{t("reset_title")}</h1>
          <p className="text-sm text-gray-500 mt-2 text-center">{t("reset_subtitle")}</p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div className="flex flex-col gap-1.5 relative">
            <label className="text-sm font-medium text-gray-700" htmlFor="password">
              {t("reset_new_password")}
            </label>
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              name="password"
              value={input.password}
              onChange={handleChange}
              className="w-full p-3 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
              required
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-[38px] text-gray-500"
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>

          <div className="flex flex-col gap-1.5 relative">
            <label className="text-sm font-medium text-gray-700" htmlFor="confirmPassword">
              {t("reset_confirm_password")}
            </label>
            <input
              id="confirmPassword"
              type={showConfirm ? "text" : "password"}
              name="confirmPassword"
              value={input.confirmPassword}
              onChange={handleChange}
              className="w-full p-3 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
              required
            />
            <button
              type="button"
              onClick={() => setShowConfirm(!showConfirm)}
              className="absolute right-3 top-[38px] text-gray-500"
            >
              {showConfirm ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>

          <div className="flex flex-col gap-3 mt-2">
            <button
              type="submit"
              disabled={loading}
              className="btn-codi-animated mt-2 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? t("reset_saving") : t("reset_submit")}
            </button>
            <Button asChild variant="outline" type="button" className="w-full py-2.5 rounded-lg">
              <Link href="/auth/login">{t("back_to_login")}</Link>
            </Button>
          </div>
        </form>
      </div>
    </main>
  );
}
