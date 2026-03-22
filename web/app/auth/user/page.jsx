"use client";

// Importaciones necesarias
import { useAuth } from "@/app/context/AuthContext";
import { useState } from "react";
import { sileo } from "sileo";
import axios from "axios";
import { Button } from "@/app/components/ui/button"; // Asegúrate de que la ruta sea correcta
import Link from "next/link";

export default function UserProfile() {
    const { user } = useAuth();

    // Estado adaptado para cambiar la contraseña en lugar del email
    const [input, setInput] = useState({
        newPassword: "",
        confirmPassword: "",
    });

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
                    
                    <div className="flex flex-col gap-1.5">
                        <label className="text-sm font-medium text-gray-700" htmlFor="newPassword">
                            Nueva contraseña
                        </label>
                        <input 
                            id="newPassword"
                            className="w-full p-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm" 
                            type="password"
                            name="newPassword"
                            value={input.newPassword}
                            onChange={handleChange}
                            placeholder="Escribe tu nueva contraseña"
                            required
                        />
                    </div>

                    <div className="flex flex-col gap-1.5">
                        <label className="text-sm font-medium text-gray-700" htmlFor="confirmPassword">
                            Confirmar contraseña
                        </label>
                        <input 
                            id="confirmPassword"
                            className="w-full p-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm" 
                            type="password"
                            name="confirmPassword"
                            value={input.confirmPassword}
                            onChange={handleChange}
                            placeholder="Repite tu nueva contraseña"
                            required
                        />
                    </div>

                    {/* Botones de acción usando tus clases personalizadas */}
                    <div className="flex flex-col gap-3 mt-4">
                        <button type="submit" className="btn-codi-animated rounded-md">
                            Guardar cambios
                        </button>

                        <Button asChild type="button" className="w-full py-2.5 rounded-md">
                            <Link href="/">Volver al inicio</Link>
                        </Button>
                    </div>
                </form>
            </div>
        </div>
    );
}