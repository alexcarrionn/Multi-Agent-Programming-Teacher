"use client";

import { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import WelcomeScreen from './WelcomeScreen';
import ChatInput from './ChatInput';

export default function ChatArea({ messages = [], isLoading = false, onSend = () => {}, onStop = () => {} }) {
    const bottomRef = useRef(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const hasMessages = messages.length > 0;

    return (
        <div className="flex h-full w-full flex-col">
            {hasMessages ? (
                <>
                    {/* ZONA DE MENSAJES (Ocupa todo el espacio disponible y tiene scroll interno) */}
                    <div className="flex-1 overflow-y-auto w-full">
                        <div className="max-w-3xl mx-auto px-4 py-6">
                            {messages.map((msg, i) => (
                                <MessageBubble
                                    key={i}
                                    message={msg}
                                    isThinking={isLoading && i === messages.length - 1}
                                />
                            ))}
                            <div ref={bottomRef} />
                        </div>
                    </div>
                    
                    {/* BARRA DE INPUT ANCLADA AL FONDO */}
                    <div className="shrink-0 w-full pb-2">
                        <ChatInput onSend={onSend} isLoading={isLoading} onStop={onStop} />
                    </div>
                </>
            ) : (
                /* ESTADO INICIAL: Todo el contenido centrado al estilo ChatGPT */
                <div className="flex h-full flex-col items-center justify-center w-full">
                    {/* -translate-y-8 lo sube ligeramente para que quede visualmente en el centro perfecto */}
                    <div className="w-full flex flex-col items-center gap-2 transform -translate-y-8">
                        <WelcomeScreen onSuggestionClick={onSend} />
                        <div className="w-full">
                            <ChatInput onSend={onSend} isLoading={isLoading} onStop={onStop} />
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}