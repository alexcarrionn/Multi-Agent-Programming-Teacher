"use client"; 
import { createContext, useContext,useState, useEffect } from "react";
import axios from "axios";

const AuthContext = createContext();

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    // Al montar comprobamos que este la sesion activa en la cookie. 
    useEffect(() => {
                axios.get("/backend/api/me", { withCredentials: true })
      .then(res => setUser(res.data))
      .catch(() => setUser(false)) 
      .finally(() => setLoading(false));
    }, []);

    const logout = async () => {
                await axios.post("/backend/api/logout", null, { withCredentials: true });
        setUser(false);
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