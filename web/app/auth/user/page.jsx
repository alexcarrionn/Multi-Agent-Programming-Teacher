"use client";

// Importaciones necesarias
import { useAuth } from "@/app/context/AuthContext";
import { useState } from "react";
import { sileo } from "sileo";
import axios from "axios";
import { Button } from "@/app/components/ui/button"; // Asegúrate de que la ruta sea correcta
import Link from "next/link";
import { Eye, EyeOff } from "lucide-react";
import { useRouter } from "next/navigation";

export default function UserProfile() {
    const { user, setUser } = useAuth();
    const router = useRouter();

    // Estado adaptado para cambiar la contraseña en lugar del email
    const [input, setInput] = useState({
        newPassword: "",
        confirmPassword: "",
    });

    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);

    // Función para manejar los errores (copiada de tus otros formularios)
    const getErrorMessage = (err) => {
        if (!err) return "Ha ocurrido un error.";
        if (typeof err === "string") return err;
        if (axios.isAxiosError(err)) {
            return (
                err.response?.data?.detail ||
                err.response?.data?.message ||
                err.message ||
                "Error de red o del servidor."
            );
        }
        return "Ha ocurrido un error.";
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setInput({
            ...input,
            [name]: value,
        });
    };

    const handleError = (err) => {
        const description = getErrorMessage(err);
        sileo.error({
            title: "Error",
            description,
        });
        if (err) {
            console.error("Error:", err);
        }
    };

    const handleSuccess = (msg) => {
        sileo.success({
            title: "Actualización exitosa",
            description: msg || "Tu perfil se ha actualizado correctamente.",
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        // Validación básica en el frontend
        if (input.newPassword !== input.confirmPassword) {
            handleError("Las contraseñas no coinciden.");
            return;
        }

        try {
            await axios.put("/backend/api/update-password", {
                password: input.newPassword
            }, { withCredentials: true });
            
            handleSuccess("Contraseña actualizada con éxito.");
            setInput({ newPassword: "", confirmPassword: "" }); // Limpiamos los campos
        } catch (error) {
            handleError(error);
        }
    };

        const handleDeleteAccount = async () => {
            
        /*if (!confirm("¿Estás seguro de que deseas eliminar tu cuenta? Esta acción no se puede deshacer.")) {
            return;
        }*/

        if (!confirm("¿Estás seguro de que deseas eliminar tu cuenta? Tus datos personales se eliminarán de forma permanente, pero tu progreso se conservará de forma anónima con fines de investigación educativa.")) {
                 return;
        }
        try {
            await axios.delete("/backend/api/delete-account", { withCredentials: true });
            await axios.post("/backend/api/logout", {}, { withCredentials: true });

            sileo.success({
                title: "Cuenta eliminada",
                description: "Tu cuenta ha sido eliminada exitosamente.",
            });

            setUser(null);
            setTimeout(() => {
                router.push("/");
            }, 1000);

        } catch (error) {
            handleError(error);
        }
     };

    //Constante para poder desactivar el boton de cambios si no se han realizado ninguno
    const isSubmitDisabled = !input.newPassword || !input.confirmPassword; 
    
    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-slate-50 p-6">
            <div className="bg-white p-8 rounded-xl shadow-lg border border-gray-100 w-full max-w-md">
                <h1 className="text-3xl font-bold mb-6 text-gray-900 text-center">Tu Perfil</h1>
                
                {/* Información estática del usuario */}
                <div className="flex flex-col gap-4 mb-8 p-4 bg-blue-50/50 rounded-lg border border-blue-100">
                    <div>
                        <span className="text-sm font-semibold text-blue-900">Nombre:</span>
                        <p className="text-gray-800">{user?.nombre || "Cargando..."}</p>
                    </div>
                    <div>
                        <span className="text-sm font-semibold text-blue-900">Correo electrónico:</span>
                        <p className="text-gray-800">{user?.email || "Cargando..."}</p>
                    </div>
                    <div>
                        <span className="text-sm font-semibold text-blue-900">Nivel actual: </span>
                        <p className="text-gray-800 capitalize">{user?.nivel || "Cargando..."}</p>
                    </div>
                </div>

                {/* Formulario para cambiar datos (ej. Contraseña) */}
                <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                    <h2 className="text-lg font-semibold text-gray-800 border-b pb-2 mb-2">Cambiar contraseña</h2>
                    <label className="text-sm font-medium text-gray-700" htmlFor="newPassword">
                        Nueva contraseña
                    </label>
                    <div className="relative">
                        <input 
                            type={showPassword ? "text" : "password"}
                            name="newPassword"
                            value={input.newPassword}
                            onChange={handleChange}
                            className="w-full p-2.5 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                            placeholder="Escribe tu nueva contraseña"
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
                        <label className="text-sm font-medium text-gray-700" htmlFor="confirmPassword" >
                            Confirmar contraseña
                        </label>
                        <div className="relative">
                        <input 
                            type={showConfirmPassword ? "text" : "password"}
                            name="confirmPassword"
                            value={input.confirmPassword}
                            onChange={handleChange}
                            className="w-full p-2.5 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                            placeholder="Escribe tu nueva contraseña"
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

                    {/* Botones de acción usando tus clases personalizadas */}
                    <div className="flex flex-col gap-3 mt-4">
                        <button type="submit" disabled={isSubmitDisabled} className="btn-codi-animated rounded-md">
                            Guardar cambios
                        </button>

                        <Button type="button" variant="destructive" onClick={handleDeleteAccount} className="w-full py-2.5 rounded-md">
                            Eliminar cuenta
                        </Button>

                        <Button asChild type="button" className="w-full py-2.5 rounded-md">
                            <Link href="/">Volver al inicio</Link>
                        </Button>
                    </div>
                </form>
            </div>
        </div>
    );
}