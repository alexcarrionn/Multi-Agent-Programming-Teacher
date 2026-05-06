"use client"; 
import { createContext, useContext,useState, useEffect } from "react";
import axios from "axios";

const AuthContext = createContext();

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    // Al montar comprobamos que este la sesion activa en la cookie. 
    useEffect(() => {
        const fetchUser = async () => {
            try {
                const res = await axios.get("/backend/api/me", { withCredentials: true });
                setUser(res.data);                      // res.data.rol === "alumno"
            } catch {
                try {
                    const res = await axios.get("/backend/api/docente/me", { withCredentials: true });
                    setUser(res.data);                  // res.data.rol === "docente"
                } catch {
                    setUser(false);
                }
            } finally {
                setLoading(false);
            }
        };
        fetchUser();
    }, []);

    const logout = async () => {
        // Dependiendo del rol del usuario, se llama a un endpoint de logout diferente 
         const endpoint = user?.rol === "docente" ? "/backend/api/docente/logout" : "/backend/api/logout";
         try {
            await axios.post(endpoint, {}, { withCredentials: true });
         }finally {
            setUser(false);
         }
    };

    return (
        <AuthContext.Provider value={{ user, loading, setUser , logout}}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    return useContext(AuthContext);
}