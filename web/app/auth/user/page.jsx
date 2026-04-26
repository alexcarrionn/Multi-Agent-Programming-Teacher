"use client";

import { useAuth } from "@/app/context/AuthContext";
import { useState } from "react";
import { sileo } from "sileo";
import axios from "axios";
import { Button } from "@/app/components/ui/button";
import Link from "next/link";
import { Eye, EyeOff } from "lucide-react";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import "@/lib/i18n";

export default function UserProfile() {
  const { user, setUser } = useAuth();
  const router = useRouter();
  const { t } = useTranslation();

  const [input, setInput] = useState({ newPassword: "", confirmPassword: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

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

    if (input.newPassword !== input.confirmPassword) {
      handleError(t("passwords_dont_match"));
      return;
    }

    try {
      await axios.put("/backend/api/update-password", { password: input.newPassword }, { withCredentials: true });
      sileo.success({ title: t("profile_update_title"), description: t("profile_password_updated") });
      setInput({ newPassword: "", confirmPassword: "" });
    } catch (error) {
      handleError(error);
    }
  };

  const handleDeleteAccount = async () => {
    if (!confirm(t("profile_delete_confirm"))) return;

    try {
      await axios.delete("/backend/api/delete-account", { withCredentials: true });
      await axios.post("/backend/api/logout", {}, { withCredentials: true });
      sileo.success({ title: t("profile_delete_title"), description: t("profile_delete_msg") });
      setUser(null);
      setTimeout(() => router.push("/"), 1000);
    } catch (error) {
      handleError(error);
    }
  };

  const isSubmitDisabled = !input.newPassword || !input.confirmPassword;

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-50 p-6">
      <div className="bg-white p-8 rounded-xl shadow-lg border border-gray-100 w-full max-w-md">
        <h1 className="text-3xl font-bold mb-6 text-gray-900 text-center">{t("profile_title")}</h1>

        <div className="flex flex-col gap-4 mb-8 p-4 bg-blue-50/50 rounded-lg border border-blue-100">
          <div>
            <span className="text-sm font-semibold text-blue-900">{t("profile_name")}</span>
            <p className="text-gray-800">{user?.nombre || t("loading")}</p>
          </div>
          <div>
            <span className="text-sm font-semibold text-blue-900">{t("profile_email")}</span>
            <p className="text-gray-800">{user?.email || t("loading")}</p>
          </div>
          <div>
            <span className="text-sm font-semibold text-blue-900">{t("profile_level")}</span>
            <p className="text-gray-800 capitalize">{user?.nivel || t("loading")}</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <h2 className="text-lg font-semibold text-gray-800 border-b pb-2 mb-2">{t("profile_change_password")}</h2>

          <label className="text-sm font-medium text-gray-700" htmlFor="newPassword">
            {t("profile_new_password")}
          </label>
          <div className="relative">
            <input
              type={showPassword ? "text" : "password"}
              name="newPassword"
              value={input.newPassword}
              onChange={handleChange}
              className="w-full p-2.5 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
              placeholder={t("profile_password_placeholder")}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500"
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-gray-700" htmlFor="confirmPassword">
              {t("profile_confirm_password")}
            </label>
            <div className="relative">
              <input
                type={showConfirmPassword ? "text" : "password"}
                name="confirmPassword"
                value={input.confirmPassword}
                onChange={handleChange}
                className="w-full p-2.5 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                placeholder={t("profile_password_placeholder")}
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500"
              >
                {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <div className="flex flex-col gap-3 mt-4">
            <button type="submit" disabled={isSubmitDisabled} className="btn-codi-animated rounded-md">
              {t("profile_save")}
            </button>
            <Button type="button" variant="destructive" onClick={handleDeleteAccount} className="w-full py-2.5 rounded-md">
              {t("profile_delete")}
            </Button>
            <Button asChild type="button" className="w-full py-2.5 rounded-md">
              <Link href="/">{t("profile_back")}</Link>
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
