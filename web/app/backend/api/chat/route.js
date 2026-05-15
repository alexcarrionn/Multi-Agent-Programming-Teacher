// Route Handler que proxea POST /backend/api/chat al backend FastAPI manteniendo
// el streaming SSE. No usar el rewrite de next.config.mjs porque buffea el body
// y el cliente se queda esperando los chunks hasta que termina todo el stream.
export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(request) {
  const body = await request.text();
  const cookieHeader = request.headers.get("cookie") ?? "";
  const backend = process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8000";

  const upstream = await fetch(`${backend}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Cookie": cookieHeader,
    },
    body,
    // duplex requerido por Node 18+ cuando se envia body
    duplex: "half",
  });

  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      "Content-Type": upstream.headers.get("content-type") ?? "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      "Connection": "keep-alive",
      "X-Accel-Buffering": "no",
      // Bloquea cualquier compresor intermedio (Next.js, proxy, etc). gzip buffea
      // el stream y se pierden los bytes no flusheados cuando la conexion se corta.
      "Content-Encoding": "identity",
    },
  });
}
