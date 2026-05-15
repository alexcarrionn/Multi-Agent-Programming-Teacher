/**
 * Tests de la funcion sendChatMessage: el wrapper que llama a /backend/api/chat
 * y devuelve el ReadableStream del SSE. Verifica que:
 *  - Hace POST con el body, headers y signal correctos.
 *  - Devuelve response.body en exito.
 *  - Lanza Error("NO_AUTH") en 401.
 *  - Lanza Error con mensaje legible en otros errores.
 */
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { sendChatMessage } from "./chat";

describe("sendChatMessage", () => {
  beforeEach(() => {
    globalThis.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  test("hace POST a /backend/api/chat con el body, headers y credenciales correctos", async () => {
    const fakeBody = new ReadableStream();
    globalThis.fetch.mockResolvedValue({
      ok: true,
      status: 200,
      body: fakeBody,
    });

    const signal = new AbortController().signal;
    const result = await sendChatMessage("hola", "Introduccion_programacion", signal);

    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
    const [url, opts] = globalThis.fetch.mock.calls[0];
    expect(url).toBe("/backend/api/chat");
    expect(opts.method).toBe("POST");
    expect(opts.headers).toEqual({ "Content-Type": "application/json" });
    expect(opts.credentials).toBe("include");
    expect(opts.signal).toBe(signal);
    expect(JSON.parse(opts.body)).toEqual({
      message: "hola",
      asignatura: "Introduccion_programacion",
    });
    expect(result).toBe(fakeBody);
  });

  test("lanza Error('NO_AUTH') cuando el backend responde 401", async () => {
    globalThis.fetch.mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: "no autenticado" }),
    });

    await expect(sendChatMessage("hola", "x")).rejects.toThrow("NO_AUTH");
  });

  test("lanza Error con detail cuando el backend responde 4xx/5xx no-401", async () => {
    globalThis.fetch.mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({ detail: "fallo interno" }),
    });

    await expect(sendChatMessage("hola", "x")).rejects.toThrow("fallo interno");
  });

  test("lanza Error con error.error si el body trae 'error' en vez de 'detail'", async () => {
    globalThis.fetch.mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({ error: "asignatura invalida" }),
    });

    await expect(sendChatMessage("hola", "x")).rejects.toThrow("asignatura invalida");
  });

  test("lanza Error con codigo HTTP si el body no es JSON parseable", async () => {
    globalThis.fetch.mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => {
        throw new Error("no es JSON");
      },
    });

    await expect(sendChatMessage("hola", "x")).rejects.toThrow("Error: 503");
  });

  test("propaga AbortError cuando el signal se aborta", async () => {
    globalThis.fetch.mockImplementation((_url, { signal }) => {
      return new Promise((_resolve, reject) => {
        signal.addEventListener("abort", () => {
          const err = new Error("aborted");
          err.name = "AbortError";
          reject(err);
        });
      });
    });

    const controller = new AbortController();
    const promise = sendChatMessage("hola", "x", controller.signal);
    controller.abort();
    await expect(promise).rejects.toMatchObject({ name: "AbortError" });
  });
});
