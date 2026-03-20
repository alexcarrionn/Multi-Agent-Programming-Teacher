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
        <div className="flex flex-col h-full">
            {hasMessages ? (
                <>
                    <div className="flex-1 overflow-y-auto">
                        <div className="max-w-3xl mx-auto px-4 py-6">
                            {messages.map((msg, i) => (
                                <MessageBubble key={i} message={msg} />
                            ))}
                            {isLoading && messages[messages.length - 1]?.role === 'user' && (
                                <div className="flex items-center gap-3 py-4">
                                    <div className="h-8 w-8 rounded-full bg-gradient-to-br from-primary/80 to-primary flex items-center justify-center">
                                        <Loader2 className="h-4 w-4 text-primary-foreground animate-spin" />
                                    </div>
                                    <div className="flex gap-1.5">
                                        <div className="w-2 h-2 rounded-full bg-muted-foreground/40 animate-bounce" style={{ animationDelay: '0ms' }} />
                                        <div className="w-2 h-2 rounded-full bg-muted-foreground/40 animate-bounce" style={{ animationDelay: '150ms' }} />
                                        <div className="w-2 h-2 rounded-full bg-muted-foreground/40 animate-bounce" style={{ animationDelay: '300ms' }} />
                                    </div>
                                </div>
                            )}
                            <div ref={bottomRef} />
                        </div>
                    </div>
                    <ChatInput onSend={onSend} isLoading={isLoading} />
                </>
            ) : (
                <div className="flex-1 flex flex-col items-center justify-center px-4">
                    <WelcomeScreen onSuggestionClick={onSend} />
                    <div className="w-full max-w-3xl mt-2">
                        <ChatInput onSend={onSend} isLoading={isLoading} />
                    </div>
                </div>
            )}
        </div>
    );
}