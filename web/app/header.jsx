import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function Header() {
{/* Vamos a poner los dos botones e inicio de sesion y de registro */}
  return (
   
    <header className="absolute top-0 right-0 p-6 flex gap-4">
        {/* Usamos Link directamente con las clases del botón y el href limpio */}
        <Button login>
            <Link href="/login">Login</Link>
        </Button>
        
        <Button register>
            <Link href="/register">Register</Link>
        </Button>
    </header>
  );
}