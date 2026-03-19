// app/page.jsx
"use client"; // Necesario porque ahora usamos estados interactivos (useState)

import { useState } from "react";
import Header from "./components/header";
import ChatArea from "./components/chat/ChatArea";

export default function Home() {
  // Estado para almacenar el historial de mensajes
  const [messages, setMessages] = useState([]);
  // Estado para simular si la IA está "pensando"
  const [isLoading, setIsLoading] = useState(false);

  // Función que se ejecuta al enviar un mensaje
  const handleSendMessage = (content) => {
    // 1. Añadimos el mensaje del usuario a la lista
    const newUserMessage = { role: "user", content };
    setMessages((prev) => [...prev, newUserMessage]);
    
    // 2. Simulamos que Codi está escribiendo
    setIsLoading(true);

    // 3. Simulamos una respuesta de la IA después de 1.5 segundos
    setTimeout(() => {
      const botResponse = { 
        role: "bot", 
        content: "¡Hola! Soy Codi. Esta es una respuesta de prueba. Pronto estaré conectado a una IA real." 
      };
      setMessages((prev) => [...prev, botResponse]);
      setIsLoading(false);
    }, 1500);
  };

  return (
    <main className="relative flex min-h-screen flex-col bg-gray-100 pt-20">
      <Header />

      <div className="flex-1 overflow-hidden">
        {/* Pasamos los estados y la función al ChatArea */}
        <ChatArea 
          messages={messages} 
          isLoading={isLoading} 
          onSend={handleSendMessage} 
        />
      </div>

      <p className="px-4 py-4 text-xs text-gray-500 text-center max-w-3xl mx-auto">
        Codi es una IA de apoyo educativo y puede cometer errores.
      </p>
    </main>
  );
}