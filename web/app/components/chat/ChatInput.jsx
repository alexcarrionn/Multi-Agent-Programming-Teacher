import { useState, useRef, useEffect } from 'react';
import { Button } from "@/app/components/ui/button";
import { Send, Square } from 'lucide-react';

export default function ChatInput({ onSend, isLoading }) {
    const [message, setMessage] = useState('');
    const textareaRef = useRef(null);

    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
        }
    }, [message]);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!message.trim() || isLoading) return;
        onSend(message.trim());
        setMessage('');
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    return (
        <div className="px-4 pb-4 pt-2">
            <form onSubmit={handleSubmit} className="max-w-3xl mx-auto relative">
                <div className="relative flex items-end bg-card border border-border rounded-2xl shadow-sm focus-within:ring-2 focus-within:ring-ring/20 focus-within:border-primary/40 transition-all">
                    <textarea
                        ref={textareaRef}
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Escribe tu mensaje..."
                        rows={1}
                        className="flex-1 resize-none bg-transparent px-4 py-3.5 pr-14 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none max-h-[200px]"
                    />
                    <div className="absolute right-2 bottom-2">
                        <Button
                            type="submit"
                            size="icon"
                            disabled={!message.trim() && !isLoading}
                            className="h-8 w-8 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground disabled:opacity-30 transition-all"
                        >
                            {isLoading
                                ? <Square className="h-3.5 w-3.5 fill-current" />
                                : <Send className="h-3.5 w-3.5" />
                            }
                        </Button>
                    </div>
                </div>
            </form>
        </div>
    );
}