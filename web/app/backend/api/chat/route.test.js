/**
 * Tests del Route Handler POST /backend/api/chat.
 * Cubre que el proxy hacia FastAPI:
 *  - Reenvia el body literal del request.
 *  - Reenvia la cookie de auth (sin esto, el backend devuelve 401).
 *  - Conserva el content-type del upstream.
 *  - Setea los headers SSE correctos para que el stream no se rompa:
 *      Content-Encoding: identity   (evita gzip que rompe SSE)
 *      Cache-Control: no-cache, no-transform
 *      X-Accel-Buffering: no
 *  - Devuelve el upstream.body como stream del response.
 *  - Propaga el status code upstream.
 */
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { POST } from "./route";

describe("POST /backend/api/chat (Route Handler)", () => {
  beforeEach(() => {
    globalThis.fetch = vi.fn();
    // El Route Handler lee la env var BACKEND_INTERNAL_URL; la fijamos para que sea predecible
    process.env.BACKEND_INTERNAL_URL = "http://api:8000";
  });

  afterEach(() => {
    vi.restoreAllMocks();
    delete process.env.BACKEND_INTERNAL_URL;
  });

  function makeRequest({ body = '{"message":"hola","asignatura":"x"}', cookie = "access_token=abc" } = {}) {
    return {
      text: async () => body,
      headers: {
        get: (name) => (name.toLowerCase() === "cookie" ? cookie : null),
      },
    };
  }

  function makeUpstreamResponse({ status = 200, contentType = "text/event-stream" } = {}) {
    const fakeBody = new ReadableStream();
    return {
      status,
      body: fakeBody,
      headers: {
        get: (name) => (name.toLowerCase() === "content-type" ? contentType : null),
      },
      _fakeBody: fakeBody, // helper para asserts
    };
  }

  test("hace fetch a {BACKEND_INTERNAL_URL}/api/chat con method POST y duplex half", async () => {
    const upstream = makeUpstreamResponse();
    globalThis.fetch.mockResolvedValue(upstream);

    await POST(makeRequest({ body: '{"message":"hola","asignatura":"x"}' }));

    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
    const [url, opts] = globalThis.fetch.mock.calls[0];
    expect(url).toBe("http://api:8000/api/chat");
    expect(opts.method).toBe("POST");
    expect(opts.duplex).toBe("half");
    expect(opts.body).toBe('{"message":"hola","asignatura":"x"}');
  });

  test("reenvia la cookie del request al backend (sin esto, 401)", async () => {
    globalThis.fetch.mockResolvedValue(makeUpstreamResponse());
    await POST(makeRequest({ cookie: "access_token=jwt-importante; otra=x" }));

    const [, opts] = globalThis.fetch.mock.calls[0];
    expect(opts.headers.Cookie).toBe("access_token=jwt-importante; otra=x");
    expect(opts.headers["Content-Type"]).toBe("application/json");
  });

  test("si la cookie es null, manda string vacio sin romperse", async () => {
    globalThis.fetch.mockResolvedValue(makeUpstreamResponse());
    const req = {
      text: async () => '{"x":1}',
      headers: { get: () => null },
    };
    await POST(req);

    const [, opts] = globalThis.fetch.mock.calls[0];
    expect(opts.headers.Cookie).toBe("");
  });

  test("devuelve el upstream.body como stream del Response", async () => {
    const upstream = makeUpstreamResponse();
    globalThis.fetch.mockResolvedValue(upstream);

    const response = await POST(makeRequest());
    expect(response.body).toBe(upstream._fakeBody);
  });

  test("propaga el status code del upstream", async () => {
    globalThis.fetch.mockResolvedValue(makeUpstreamResponse({ status: 502 }));

    const response = await POST(makeRequest());
    expect(response.status).toBe(502);
  });

  test("setea headers SSE-friendly (identity, no-cache, x-accel-buffering)", async () => {
    globalThis.fetch.mockResolvedValue(makeUpstreamResponse());
    const response = await POST(makeRequest());

    // Estos tres son criticos para que el SSE funcione: gzip rompe streaming
    expect(response.headers.get("Content-Encoding")).toBe("identity");
    expect(response.headers.get("Cache-Control")).toBe("no-cache, no-transform");
    expect(response.headers.get("X-Accel-Buffering")).toBe("no");
    expect(response.headers.get("Connection")).toBe("keep-alive");
  });

  test("conserva el content-type del upstream", async () => {
    globalThis.fetch.mockResolvedValue(makeUpstreamResponse({ contentType: "text/event-stream; charset=utf-8" }));
    const response = await POST(makeRequest());

    expect(response.headers.get("Content-Type")).toBe("text/event-stream; charset=utf-8");
  });

  test("usa text/event-stream por defecto si el upstream no manda content-type", async () => {
    const upstream = {
      status: 200,
      body: new ReadableStream(),
      headers: { get: () => null }, // no content-type
    };
    globalThis.fetch.mockResolvedValue(upstream);

    const response = await POST(makeRequest());
    expect(response.headers.get("Content-Type")).toBe("text/event-stream");
  });
});
