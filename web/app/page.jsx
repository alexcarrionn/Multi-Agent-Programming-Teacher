// app/page.jsx
"use client";

import { useState } from "react";
import Header from "./components/ui/header";
import ChatArea from "./components/chat/ChatArea";

export default function Home() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = (content) => {
    const newUserMessage = { role: "user", content };
    setMessages((prev) => [...prev, newUserMessage]);
    
    setIsLoading(true);

    setTimeout(() => {
      const botResponse = { 
        role: "bot", 
        content: "¡Hola! Soy Codi. Esta es una respuesta de prueba. Pronto estaré conectado a una IA real." 
      };
      setMessages((prev) => [...prev, botResponse]);
      setIsLoading(false);
    }, 3000);
  };

  return (
    // CAMBIO CLAVE: Usamos h-dvh en lugar de min-h-dvh para anclar el tamaño a la pantalla
    <main className="flex h-dvh flex-col overflow-hidden bg-gray-50">
      
      {/* Header fijo arriba */}
      <div className="shrink-0 border-b border-gray-200 bg-white">
        <Header />
      </div>

      {/* Contenedor central. Flex-1 toma el espacio restante, min-h-0 evita desbordamientos */}
      <div className="relative flex-1 min-h-0 w-full">
        <ChatArea 
          messages={messages} 
          isLoading={isLoading} 
          onSend={handleSendMessage} 
        />
      </div>

      {/* Footer fijo abajo */}
      <div className="shrink-0 flex items-center justify-center bg-gray-50 px-4 py-2">
        <p className="text-xs text-gray-500 text-center max-w-3xl">
          Codi es una IA de apoyo educativo y puede cometer errores.
        </p>
      </div>
    </main>
  );
}