  "use client";
  import { useEffect } from "react";
  import { useRouter } from "next/navigation";
  import { useAuth } from "@/app/context/AuthContext";

  export default function DocenteLayout({ children }) {
    const { user, loading } = useAuth();
    const router = useRouter();

    useEffect(() => {
      if (loading) return;
      if (!user || user.rol !== "docente") router.replace("/auth/docente/login");
    }, [user, loading, router]);

    if (loading || !user || user.rol !== "docente") return null;
    return <>{children}</>;
  }