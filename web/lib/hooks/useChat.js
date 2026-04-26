/* Esta clase nos va a permitir gestionar la comunicación con el backend para el chat */
"use client";

import { useRouter } from "next/navigation";
import { sendChatMessage as sendMessageApi } from "@/lib/api/chat";
import { useRef, useCallback, useState } from "react";
import { useAuth } from "@/app/context/AuthContext";

export function useChat() {
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const abortControllerRef = useRef(null);
    const router = useRouter();
    const {user} = useAuth();

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
            const stream = await sendMessageApi(message, user?.asignatura ?? "Introduccion_programacion", abortControllerRef.current.signal);
            if (!stream) throw new Error("EMPTY_STREAM");
            const reader = stream.getReader();
            const decoder = new TextDecoder();

            let buffer = "";
            let streamFinished = false;

            const applyBotChunk = (parsed) => {
                setMessages(prev => {
                    const updated = [...prev];
                    const last = updated[updated.length - 1];
                    if (!last || last.role !== "bot") return updated;

                    const chunkContent = typeof parsed.content === "string" ? parsed.content : "";
                    const chunkError = typeof parsed.error === "string" ? parsed.error : "";

                    if (!chunkContent && !chunkError && !parsed.agent) return updated;

                    updated[updated.length - 1] = {
                        ...last,
                        content: chunkError || (last.content + chunkContent),
                        agent: parsed.agent ?? last.agent,
                    };
                    return updated;
                });
            };

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });

                // Procesamos eventos SSE completos (separados por línea en blanco)
                const events = buffer.split("\n\n");
                buffer = events.pop() ?? "";

                for (const evt of events) {
                    const dataLines = evt
                        .split("\n")
                        .filter((line) => line.startsWith("data:"))
                        .map((line) => line.slice(5).trim());

                    if (dataLines.length === 0) continue;

                    const rawData = dataLines.join("\n");
                    if (rawData === "[DONE]") {
                        streamFinished = true;
                        break;
                    }

                    try {
                        const parsed = JSON.parse(rawData);
                        applyBotChunk(parsed);
                    } catch {
                        // Si llega texto suelto, lo tratamos como contenido plano
                        applyBotChunk({ content: rawData });
                    }
                }

                if (streamFinished) break;
            }

            // Si queda un bloque parcial al final, intentamos procesarlo.
            if (buffer.trim().startsWith("data:")) {
                const rawData = buffer.replace(/^data:\s*/, "").trim();
                if (rawData && rawData !== "[DONE]") {
                    try {
                        applyBotChunk(JSON.parse(rawData));
                    } catch {
                        applyBotChunk({ content: rawData });
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
    }, [isLoading, router, user]);

    const stopStreaming = useCallback(() => {
        abortControllerRef.current?.abort();
    }, []);

    return { messages, isLoading, sendMessage, stopStreaming };
}