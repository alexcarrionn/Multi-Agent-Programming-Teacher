import Image from "next/image";
import Link from "next/link";
import { Button } from "@/app/components/ui/button";

export default function Header() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 px-6 py-4 flex items-center justify-between">
      <Link href="/" className="flex items-center gap-3">
        <Image src="/logo.svg" alt="Logo" width={36} height={36} priority />
        <span className="text-2xl font-bold text-gray-800">Codi</span>
      </Link>

      <div className="flex gap-4">
        <Button asChild variant="default" className="bg-blue-600 hover:bg-blue-700">
          <Link href="/components/login">Iniciar sesión</Link>
        </Button>

        <Button asChild variant="default" className="bg-green-600 hover:bg-green-700">
          <Link href="/components/register">Registrarse</Link>
        </Button>
      </div>
    </header>
  );
}