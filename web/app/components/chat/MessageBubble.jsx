"use client";

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Button } from "@/app/components/ui/button"; // Asegúrate de que esta ruta sea correcta
import { Copy, Check, Zap, CheckCircle2, AlertCircle, Loader2, ChevronRight, Clock, User, Sparkles } from 'lucide-react';
import { cn } from "@/lib/utils"; // Importamos la utilidad que creamos en el Paso 2
import { sileo } from "sileo";

const FunctionDisplay = ({ toolCall }) => {
    const [expanded, setExpanded] = useState(false);
    const name = toolCall?.name || 'Function';
    const status = toolCall?.status || 'pending';
    const results = toolCall?.results;

    const parsedResults = (() => {
        if (!results) return null;
        try { return typeof results === 'string' ? JSON.parse(results) : results; }
        catch { return results; }
    })();

    const isError = results && (
        (typeof results === 'string' && /error|failed/i.test(results)) ||
        (parsedResults?.success === false)
    );

    const statusConfig = {
        pending: { icon: Clock, color: 'text-muted-foreground', text: 'Pendiente' },
        running: { icon: Loader2, color: 'text-primary', text: 'Ejecutando...', spin: true },
        in_progress: { icon: Loader2, color: 'text-primary', text: 'Ejecutando...', spin: true },
        completed: isError
            ? { icon: AlertCircle, color: 'text-destructive', text: 'Error' }
            : { icon: CheckCircle2, color: 'text-green-600', text: 'Completado' },
        success: { icon: CheckCircle2, color: 'text-green-600', text: 'Completado' },
        failed: { icon: AlertCircle, color: 'text-destructive', text: 'Error' },
        error: { icon: AlertCircle, color: 'text-destructive', text: 'Error' }
    }[status] || { icon: Zap, color: 'text-muted-foreground', text: '' };

    const Icon = statusConfig.icon;

    return (
        <div className="mt-2 text-xs">
            <button
                onClick={() => setExpanded(!expanded)}
                className={cn(
                    "flex items-center gap-2 px-3 py-1.5 rounded-lg border transition-all",
                    "hover:bg-accent",
                    expanded ? "bg-accent border-border" : "bg-card border-border"
                )}
            >
                <Icon className={cn("h-3 w-3", statusConfig.color, statusConfig.spin && "animate-spin")} />
                <span className="text-foreground">{name}</span>
                {statusConfig.text && (
                    <span className={cn("text-muted-foreground", isError && "text-destructive")}>
                        · {statusConfig.text}
                    </span>
                )}
                {!statusConfig.spin && (toolCall.arguments_string || results) && (
                    <ChevronRight className={cn("h-3 w-3 text-muted-foreground transition-transform ml-auto", expanded && "rotate-90")} />
                )}
            </button>
            {expanded && !statusConfig.spin && (
                <div className="mt-1.5 ml-3 pl-3 border-l-2 border-border space-y-2">
                    {toolCall.arguments_string && (
                        <div>
                            <div className="text-xs text-muted-foreground mb-1">Parámetros:</div>
                            <pre className="bg-muted rounded-md p-2 text-xs text-foreground whitespace-pre-wrap">
                                {(() => { try { return JSON.stringify(JSON.parse(toolCall.arguments_string), null, 2); } catch { return toolCall.arguments_string; } })()}
                            </pre>
                        </div>
                    )}
                    {parsedResults && (
                        <div>
                            <div className="text-xs text-muted-foreground mb-1">Resultado:</div>
                            <pre className="bg-muted rounded-md p-2 text-xs text-foreground whitespace-pre-wrap max-h-48 overflow-auto">
                                {typeof parsedResults === 'object' ? JSON.stringify(parsedResults, null, 2) : parsedResults}
                            </pre>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default function MessageBubble({ message }) {
    const isUser = message.role === 'user';
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(message.content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className={cn("group flex gap-3 py-4", isUser ? "flex-row-reverse" : "flex-row")}>
            <div className={cn(
                "h-8 w-8 rounded-full flex items-center justify-center shrink-0 mt-0.5",
                isUser ? "bg-blue-600" : "bg-green-600" // Cambiado a colores de tu proyecto
            )}>
                {isUser
                    ? <User className="h-4 w-4 text-white" />
                    : <Sparkles className="h-4 w-4 text-white" />
                }
            </div>

            <div className={cn("max-w-[80%] min-w-0", isUser && "flex flex-col items-end")}>
                <div className={cn(
                    "rounded-2xl px-4 py-3 text-sm leading-relaxed",
                    isUser
                        ? "bg-blue-600 text-white rounded-tr-sm" // Ajustado al azul de usuario
                        : "bg-white border border-gray-200 text-gray-800 rounded-tl-sm shadow-sm" // Ajustado al blanco del bot
                )}>
                    {isUser ? (
                        <p className="whitespace-pre-wrap">{message.content}</p>
                    ) : (
                        <ReactMarkdown
                            className="prose prose-sm max-w-none dark:prose-invert [&>*:first-child]:mt-0 [&>*:last-child]:mb-0"
                            components={{
                                code: ({ inline, className, children, ...props }) => {
                                    const match = /language-(\w+)/.exec(className || '');
                                    return !inline && match ? (
                                        <div className="relative group/code my-3">
                                            <div className="flex items-center justify-between bg-gray-800 rounded-t-lg px-3 py-1.5 text-xs text-gray-300 border border-b-0 border-gray-700">
                                                <span>{match[1]}</span>
                                                <Button size="icon" variant="ghost" className="h-5 w-5 hover:bg-gray-700 hover:text-white"
                                                    onClick={() => {
                                                        navigator.clipboard.writeText(String(children).replace(/\n$/, ''));
                                                        sileo.success({
                                                            title: 'Copiado',
                                                            description: 'Código copiado al portapapeles.',
                                                        });
                                                    }}>
                                                    <Copy className="h-3 w-3" />
                                                </Button>
                                            </div>
                                            <pre className="bg-gray-900 rounded-b-lg p-3 overflow-x-auto border border-t-0 border-gray-700 text-gray-100">
                                                <code className={className} {...props}>{children}</code>
                                            </pre>
                                        </div>
                                    ) : (
                                        <code className="px-1.5 py-0.5 rounded-md bg-gray-100 text-pink-600 text-xs font-mono">{children}</code>
                                    );
                                },
                                a: ({ children, ...props }) => <a {...props} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline underline-offset-2">{children}</a>,
                                p: ({ children }) => <p className="my-2 leading-relaxed">{children}</p>,
                                ul: ({ children }) => <ul className="my-2 ml-4 list-disc space-y-1">{children}</ul>,
                                ol: ({ children }) => <ol className="my-2 ml-4 list-decimal space-y-1">{children}</ol>,
                                li: ({ children }) => <li className="leading-relaxed">{children}</li>,
                                h1: ({ children }) => <h1 className="text-lg font-bold text-gray-900 mt-4 mb-2">{children}</h1>,
                                h2: ({ children }) => <h2 className="text-base font-bold text-gray-900 mt-3 mb-2">{children}</h2>,
                                h3: ({ children }) => <h3 className="text-sm font-bold text-gray-900 mt-3 mb-1">{children}</h3>,
                                blockquote: ({ children }) => <blockquote className="border-l-4 border-blue-500 bg-blue-50 pl-3 py-1 my-2 text-gray-700 italic rounded-r-lg">{children}</blockquote>,
                            }}
                        >
                            {message.content}
                        </ReactMarkdown>
                    )}
                </div>

                {message.tool_calls?.length > 0 && (
                    <div className="space-y-1 mt-1">
                        {message.tool_calls.map((toolCall, idx) => (
                            <FunctionDisplay key={idx} toolCall={toolCall} />
                        ))}
                    </div>
                )}

                {!isUser && message.content && (
                    <Button
                        size="icon"
                        variant="ghost"
                        className="h-7 w-7 mt-1 opacity-0 group-hover:opacity-100 transition-opacity text-gray-400 hover:text-gray-700"
                        onClick={handleCopy}
                    >
                        {copied ? <Check className="h-3.5 w-3.5 text-green-600" /> : <Copy className="h-3.5 w-3.5" />}
                    </Button>
                )}
            </div>
        </div>
    );
}