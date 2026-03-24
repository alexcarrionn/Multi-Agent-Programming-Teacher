"use client";

import { useEffect, useRef } from 'react';
import { Loader2 } from 'lucide-react';
import MessageBubble from './MessageBubble';
import WelcomeScreen from './WelcomeScreen';
import ChatInput from './ChatInput';

export default function ChatArea({ messages = [], isLoading = false, onSend = () => {} }) {
    const bottomRef = useRef(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const hasMessages = messages && messages.length > 0;

    return (
        <div className="flex h-full w-full flex-col">
            {hasMessages ? (
                <>
                    {/* ZONA DE MENSAJES (Ocupa todo el espacio disponible y tiene scroll interno) */}
                    <div className="flex-1 overflow-y-auto w-full">
                        <div className="max-w-3xl mx-auto px-4 py-6">
                            {messages.map((msg, i) => (
                                <MessageBubble key={i} message={msg} />
                            ))}
                            {isLoading && messages[messages.length - 1]?.role === 'user' && (
                                <div className="flex items-center gap-3 py-4">
                                    <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
                                        <Loader2 className="h-4 w-4 text-white animate-spin" />
                                    </div>
                                    <div className="flex gap-1.5">
                                        <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                                        <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                                        <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                                    </div>
                                </div>
                            )}
                            <div ref={bottomRef} />
                        </div>
                    </div>
                    
                    {/* BARRA DE INPUT ANCLADA AL FONDO */}
                    <div className="shrink-0 w-full pb-2">
                        <ChatInput onSend={onSend} isLoading={isLoading} />
                    </div>
                </>
            ) : (
                /* ESTADO INICIAL: Todo el contenido centrado al estilo ChatGPT */
                <div className="flex h-full flex-col items-center justify-center w-full">
                    {/* -translate-y-8 lo sube ligeramente para que quede visualmente en el centro perfecto */}
                    <div className="w-full flex flex-col items-center gap-2 transform -translate-y-8">
                        <WelcomeScreen onSuggestionClick={onSend} />
                        <div className="w-full">
                            <ChatInput onSend={onSend} isLoading={isLoading} />
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}