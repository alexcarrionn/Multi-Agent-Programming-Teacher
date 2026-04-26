"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/app/components/ui/button";
import axios from "axios";
import Image from "next/image";
import { sileo } from "sileo";
import { useTranslation } from "react-i18next";
import "@/lib/i18n";

export default function Register() {
  const router = useRouter();
  const { t } = useTranslation();
  const [input, setInput] = useState({
    nombre: "",
    email: "",
    password: "",
    confirmPassword: "",
    nivel: "",
  });

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
    setInput({ ...input, [name]: value });
  };

  const handleError = (err) => {
    sileo.error({ title: t("error"), description: getErrorMessage(err) });
    if (err) console.error("Error:", err);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (input.password !== input.confirmPassword) {
      handleError(t("passwords_dont_match"));
      return;
    }

    try {
      const { data } = await axios.post(
        "/backend/api/register",
        { nombre: input.nombre, email: input.email, password: input.password, nivel: input.nivel },
        { withCredentials: true }
      );

      sileo.success({ title: t("register_success_title"), description: data?.message || t("register_success_msg") });
      setTimeout(() => router.push("/auth/login"), 1500);
    } catch (error) {
      handleError(error);
    }

    setInput({ nombre: "", email: "", password: "", confirmPassword: "", nivel: "" });
  };

  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center p-6 bg-gray-100 py-12">
      <div className="w-full max-w-md bg-white p-8 rounded-xl shadow-lg border border-gray-100">
        <div className="flex flex-col items-center mb-6">
          <Image src="/logo.svg" alt="Logo de Codi" width={48} height={48} priority className="mb-4" />
          <h1 className="text-3xl font-bold text-gray-900 text-center">{t("register_title")}</h1>
          <p className="text-sm text-gray-500 mt-2 text-center">{t("register_subtitle")}</p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-gray-700" htmlFor="nombre">
              {t("register_name")}
            </label>
            <input
              id="nombre"
              className="w-full p-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm"
              type="text"
              name="nombre"
              value={input.nombre}
              onChange={handleChange}
              required
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-gray-700" htmlFor="email">
              {t("register_email")}
            </label>
            <input
              id="email"
              className="w-full p-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm"
              type="email"
              name="email"
              value={input.email}
              onChange={handleChange}
              required
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-gray-700" htmlFor="password">
                {t("register_password")}
              </label>
              <input
                id="password"
                className="w-full p-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm"
                type="text"
                name="password"
                value={input.password}
                onChange={handleChange}
                required
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-gray-700" htmlFor="confirmPassword">
                {t("register_confirm_password")}
              </label>
              <input
                id="confirmPassword"
                className="w-full p-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm"
                type="text"
                name="confirmPassword"
                value={input.confirmPassword}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-gray-700" htmlFor="nivel">
              {t("register_level")}
            </label>
            <select
              id="nivel"
              name="nivel"
              value={input.nivel}
              onChange={handleChange}
              className="w-full p-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm bg-white"
              required
            >
              <option value="" disabled>{t("register_level_placeholder")}</option>
              <option value="principiante">{t("register_level_beginner")}</option>
              <option value="intermedio">{t("register_level_intermediate")}</option>
              <option value="avanzado">{t("register_level_advanced")}</option>
            </select>
          </div>

          <div className="flex flex-col gap-3 mt-4">
            <button type="submit" className="btn-codi-animated mt-4">
              {t("register_submit")}
            </button>
            <Button asChild variant="outline" type="button" className="w-full py-2.5 rounded-lg">
              <Link href="/">{t("cancel")}</Link>
            </Button>
          </div>

          <p className="mt-2 text-sm text-gray-600 text-center">
            {t("register_has_account")}{" "}
            <Link href="/auth/login" className="text-blue-600 font-semibold hover:underline">
              {t("register_login_link")}
            </Link>.
          </p>
        </form>
      </div>
    </main>
  );
}
