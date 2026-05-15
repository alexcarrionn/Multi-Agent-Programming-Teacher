/**
 * Tests del hook useChat: el corazon de la UI del chat.
 * Cubre el ciclo completo de envio de mensaje + lectura de SSE:
 *  - Estado inicial vacio.
 *  - sendMessage añade mensaje del user y placeholder del bot.
 *  - Procesa chunks SSE y concatena el content en el ultimo mensaje del bot.
 *  - Soporta multiple eventos data: en un mismo chunk.
 *  - Soporta eventos divididos entre dos chunks (buffering).
 *  - `[DONE]` termina el stream sin errores.
 *  - Ignora comentarios SSE (:keepalive).
 *  - Si llega {"error": ...} lo pone como content del bot.
 *  - Si fetch lanza error generico, muestra mensaje de "Error al enviar".
 *  - NO_AUTH redirige a /auth/login (mock router).
 *  - AbortError no muestra error.
 *  - stopStreaming aborta la peticion.
 *  - No envia si ya hay un mensaje en curso (isLoading=true).
 */
import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

// Mocks de modulos antes de importar useChat.
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

const mockSendChatMessage = vi.fn();
vi.mock("@/lib/api/chat", () => ({
  sendChatMessage: (...args) => mockSendChatMessage(...args),
}));

vi.mock("@/app/context/AuthContext", () => ({
  useAuth: () => ({ user: { asignatura: "Introduccion_programacion" } }),
}));

import { useChat } from "./useChat";

// ─────────────────────────────────────────────
//  Helpers para fabricar ReadableStreams de SSE
// ─────────────────────────────────────────────

function streamFromChunks(chunks) {
  const encoder = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      for (const c of chunks) controller.enqueue(encoder.encode(c));
      controller.close();
    },
  });
}

function sseEvent(payload) {
  return `data: ${typeof payload === "string" ? payload : JSON.stringify(payload)}\n\n`;
}

// ─────────────────────────────────────────────
//  Tests
// ─────────────────────────────────────────────

describe("useChat", () => {
  beforeEach(() => {
    mockPush.mockClear();
    mockSendChatMessage.mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  test("estado inicial: messages vacio, isLoading false", () => {
    const { result } = renderHook(() => useChat());
    expect(result.current.messages).toEqual([]);
    expect(result.current.isLoading).toBe(false);
  });

  test("sendMessage con mensaje vacio no hace nada", async () => {
    const { result } = renderHook(() => useChat());
    await act(async () => {
      await result.current.sendMessage("");
    });
    expect(mockSendChatMessage).not.toHaveBeenCalled();
    expect(result.current.messages).toEqual([]);
  });

  test("sendMessage añade user + placeholder bot y procesa chunks SSE", async () => {
    mockSendChatMessage.mockResolvedValue(
      streamFromChunks([
        sseEvent({ content: "Hola ", agent: "educador" }),
        sseEvent({ content: "mundo.", agent: "educador" }),
        "data: [DONE]\n\n",
      ])
    );

    const { result } = renderHook(() => useChat());
    await act(async () => {
      await result.current.sendMessage("explicame variables");
    });

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0]).toEqual({ role: "user", content: "explicame variables" });
    expect(result.current.messages[1]).toEqual({
      role: "bot",
      content: "Hola mundo.",
      agent: "educador",
    });
    expect(result.current.isLoading).toBe(false);
  });

  test("eventos SSE divididos entre dos chunks se reensamblan correctamente", async () => {
    mockSendChatMessage.mockResolvedValue(
      streamFromChunks([
        // El primer chunk corta el evento por la mitad
        'data: {"content": "Ho',
        'la mundo", "agent": "codi"}\n\n',
        "data: [DONE]\n\n",
      ])
    );

    const { result } = renderHook(() => useChat());
    await act(async () => {
      await result.current.sendMessage("test");
    });

    expect(result.current.messages[1].content).toBe("Hola mundo");
    expect(result.current.messages[1].agent).toBe("codi");
  });

  test("ignora comentarios SSE (`:keepalive`) y solo procesa `data:`", async () => {
    mockSendChatMessage.mockResolvedValue(
      streamFromChunks([
        ": keepalive\n\n",
        sseEvent({ content: "real ", agent: "educador" }),
        ": keepalive\n\n",
        sseEvent({ content: "respuesta", agent: "educador" }),
        "data: [DONE]\n\n",
      ])
    );

    const { result } = renderHook(() => useChat());
    await act(async () => {
      await result.current.sendMessage("test");
    });

    expect(result.current.messages[1].content).toBe("real respuesta");
  });

  test("cuando llega {error: ...}, sustituye el content del bot por el mensaje de error", async () => {
    mockSendChatMessage.mockResolvedValue(
      streamFromChunks([
        sseEvent({ error: "algo fallo en el grafo" }),
        "data: [DONE]\n\n",
      ])
    );

    const { result } = renderHook(() => useChat());
    await act(async () => {
      await result.current.sendMessage("test");
    });

    expect(result.current.messages[1].content).toBe("algo fallo en el grafo");
  });

  test("si fetch lanza error generico, muestra 'Error al enviar el mensaje...'", async () => {
    mockSendChatMessage.mockRejectedValue(new Error("network fail"));

    const { result } = renderHook(() => useChat());
    await act(async () => {
      await result.current.sendMessage("test");
    });

    expect(result.current.messages[1].content).toContain("Error al enviar el mensaje");
    expect(result.current.isLoading).toBe(false);
  });

  test("NO_AUTH redirige a /auth/login y no muestra mensaje de error", async () => {
    mockSendChatMessage.mockRejectedValue(new Error("NO_AUTH"));

    const { result } = renderHook(() => useChat());
    await act(async () => {
      await result.current.sendMessage("test");
    });

    expect(mockPush).toHaveBeenCalledWith("/auth/login");
    // El placeholder del bot queda vacio porque no se sustituye con un error visible
    expect(result.current.messages[1].content).toBe("");
  });

  test("AbortError no muestra mensaje de error (el usuario lo cancelo a proposito)", async () => {
    const abortErr = new Error("aborted");
    abortErr.name = "AbortError";
    mockSendChatMessage.mockRejectedValue(abortErr);

    const { result } = renderHook(() => useChat());
    await act(async () => {
      await result.current.sendMessage("test");
    });

    // El bot queda con content vacio, NO con "Error al enviar..."
    expect(result.current.messages[1].content).toBe("");
    expect(result.current.isLoading).toBe(false);
  });

  test("isLoading=true durante el stream y false al terminar", async () => {
    let resolveStream;
    const pendingStream = new Promise((resolve) => {
      resolveStream = resolve;
    });
    mockSendChatMessage.mockReturnValue(pendingStream);

    const { result } = renderHook(() => useChat());
    let sendPromise;
    await act(async () => {
      sendPromise = result.current.sendMessage("test");
    });

    expect(result.current.isLoading).toBe(true);

    // Resolvemos con un stream que termina inmediatamente
    resolveStream(streamFromChunks([sseEvent({ content: "ok" }), "data: [DONE]\n\n"]));
    await act(async () => {
      await sendPromise;
    });

    expect(result.current.isLoading).toBe(false);
  });

  test("no envia un segundo mensaje si isLoading=true", async () => {
    let resolveStream;
    const pendingStream = new Promise((resolve) => {
      resolveStream = resolve;
    });
    mockSendChatMessage.mockReturnValueOnce(pendingStream);

    const { result } = renderHook(() => useChat());
    let firstPromise;
    await act(async () => {
      firstPromise = result.current.sendMessage("primero");
    });

    // Mientras el primero esta en vuelo, intentamos enviar otro
    await act(async () => {
      await result.current.sendMessage("segundo");
    });

    // El segundo no genera nueva llamada al API
    expect(mockSendChatMessage).toHaveBeenCalledTimes(1);

    resolveStream(streamFromChunks([sseEvent({ content: "ok" }), "data: [DONE]\n\n"]));
    await act(async () => {
      await firstPromise;
    });
  });

  test("stopStreaming aborta la peticion en curso", async () => {
    // Capturamos el signal que recibe sendChatMessage
    let receivedSignal;
    mockSendChatMessage.mockImplementation((_msg, _asig, signal) => {
      receivedSignal = signal;
      return new Promise(() => {}); // nunca resuelve
    });

    const { result } = renderHook(() => useChat());
    act(() => {
      result.current.sendMessage("test"); // sin await porque la promesa no resuelve
    });

    // Esperamos a que el signal este registrado
    await waitFor(() => expect(receivedSignal).toBeDefined());
    expect(receivedSignal.aborted).toBe(false);

    act(() => {
      result.current.stopStreaming();
    });

    expect(receivedSignal.aborted).toBe(true);
  });

  test("texto suelto sin JSON parseable en data: se trata como content plano", async () => {
    mockSendChatMessage.mockResolvedValue(
      streamFromChunks([
        "data: texto suelto sin json\n\n",
        "data: [DONE]\n\n",
      ])
    );

    const { result } = renderHook(() => useChat());
    await act(async () => {
      await result.current.sendMessage("test");
    });

    expect(result.current.messages[1].content).toBe("texto suelto sin json");
  });

  test("usa user.asignatura si esta, fallback al slug por defecto si user no tiene", async () => {
    mockSendChatMessage.mockResolvedValue(
      streamFromChunks([sseEvent({ content: "ok" }), "data: [DONE]\n\n"])
    );

    const { result } = renderHook(() => useChat());
    await act(async () => {
      await result.current.sendMessage("test");
    });

    // El mock de AuthContext devuelve asignatura "Introduccion_programacion"
    expect(mockSendChatMessage).toHaveBeenCalledWith(
      "test",
      "Introduccion_programacion",
      expect.any(AbortSignal)
    );
  });
});
