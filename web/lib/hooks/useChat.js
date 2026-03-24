/* Esta clase nos va a permitir gestionar la comunicación con el backend para el chat */
"use client";

import { useRouter } from "next/navigation";
import { sendChatMessage as sendMessageApi } from "@/lib/api/chat";
import { useRef, useCallback, useState } from "react";

export function useChat() {
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const abortControllerRef = useRef(null);
    const router = useRouter();

    const sendMessage = useCallback(async (message) => {
        if (!message.trim() || isLoading) return; // No enviar mensajes vacíos o mientras se está cargando

        // Añadimos en una sola actualización el mensaje del usuario y el placeholder del bot.
        setMessages(prev => [
            ...prev,
            { role: "user", content: message },
            { role: "bot", content: "", agent: null }
        ]);
        setIsLoading(true);

        // Creamos un nuevo AbortController para esta solicitud

        abortControllerRef.current = new AbortController();

        try {
            const stream = await sendMessageApi(message, abortControllerRef.current.signal);
            if (!stream) throw new Error("EMPTY_STREAM");
            const reader = stream.getReader();
            const decoder = new TextDecoder();

            let buffer = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });

                //Dividimos por lineas y dejamos la ultima incompleta en el buffer
                const lines = buffer.split("\n");
                buffer = lines.pop();

                // Procesamos cada linea que empiece por "data: "
                for (const line of lines) {
                    if (!line.startsWith("data: ")) continue;

                    // Extraemos el contenido después de "data: "
                    const rawData = line.slice(6).trim();
                    //Si en el conenido recibimos el evento [DONE], significa que el backend ha terminado de enviar mensajes, por lo que salimos del bucle
                    if (rawData === "[DONE]") {
                        break;
                    }

                    try {
                        const parsed = JSON.parse(rawData);
                        // Actualizamos el último mensaje del bot con el nuevo contenido y el agente
                        setMessages(prev => {
                            const updated = [...prev];
                            const last = updated[updated.length - 1];
                            if (last?.role === "bot") {
                                updated[updated.length - 1] = {
                                    ...last,
                                    content: last.content + (parsed.content ?? ""),
                                    agent: parsed.agent ?? last.agent,
                                };
                            }
                            return updated;
                        });
                    } catch {
                        // chunk malformado → lo ignoramos
                    }
                }
            }
        } catch (error) {
            if (error.message === "NO_AUTH") {
                router.push("/auth/login");
            } else if (error.name == "AbortError") {
                // Si la solicitud fue abortada, no hacemos nada
            } else {
                //sustituimos el mensaje del bot por un mensaje de error
                setMessages(prev => {
                    const updated = [...prev];
                    const last = updated[updated.length - 1];
                    if (last?.role === "bot" && last.content === "") {
                        updated[updated.length - 1] = {
                            ...last,
                            content: "Error al enviar el mensaje. Por favor, inténtalo de nuevo.",
                            agent: null
                        };
                    }
                    return updated;
                });
            }
        } finally {
            setIsLoading(false);
            abortControllerRef.current = null;
        }
    }, [isLoading, router]);

    const stopStreaming = useCallback(() => {
        abortControllerRef.current?.abort();
    }, []);

    return { messages, isLoading, sendMessage, stopStreaming };
}