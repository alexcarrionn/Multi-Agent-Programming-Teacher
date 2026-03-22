// app/page.jsx
"use client"; // Necesario porque ahora usamos estados interactivos (useState)

import { useState } from "react";
import Header from "./components/ui/header";
import ChatArea from "./components/chat/ChatArea";

export default function Home() {
  // Estado para almacenar el historial de mensajes
  const [messages, setMessages] = useState([]);
  // Estado para simular si la IA está "pensando"
  const [isLoading, setIsLoading] = useState(false);

  // Función que se ejecuta al enviar un mensaje
  const handleSendMessage = (content) => {
    // Añadimos el mensaje del usuario a la lista
    const newUserMessage = { role: "user", content };
    setMessages((prev) => [...prev, newUserMessage]);
    
    // Simulamos que Codi está escribiendo
    setIsLoading(true);

    //Simulamos una respuesta de la IA después de 3 segundos
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
    <main className="flex min-h-dvh flex-col overflow-hidden bg-gray-50">
      <div className="border-b border-gray-200 bg-white">
        <Header />
      </div>

      <div className="relative flex-1 min-h-0 overflow-hidden">
        {/* Pasamos los estados y la función al ChatArea */}
        <ChatArea 
          messages={messages} 
          isLoading={isLoading} 
          onSend={handleSendMessage} 
        />
      </div>

      <div className="flex items-center justify-center border-t border-gray-200 bg-white px-4 py-3">
        <p className="text-xs text-gray-500 text-center max-w-3xl">
          Codi es una IA de apoyo educativo y puede cometer errores.
        </p>
      </div>
    </main>
  );
}