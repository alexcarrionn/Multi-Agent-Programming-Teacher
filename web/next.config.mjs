/** @type {import('next').NextConfig} */
const nextConfig = {
  allowedDevOrigins: [
    "*.trycloudflare.com",
  ],

  // gzip rompe el streaming SSE del chat: buffea bytes hasta acumular suficientes
  // para comprimir, y si la conexion se corta se pierden los bytes no flusheados
  // (mensaje cortado a mitad o no llega nada). Para SSE necesitamos identity.
  // Si en el futuro hay un nginx delante, que se encargue el de comprimir lo demas.
  compress: false,

  experimental: {
    proxyClientMaxBodySize: "50mb",
  },

  async headers() {
    const isDev = process.env.NODE_ENV !== "production";
    // CSP pragmatico: 'unsafe-inline' en scripts/estilos porque Next hidrata con
    // inline; el XSS principal (HTML crudo) ya esta cubierto porque react-markdown
    // no renderiza HTML. En dev relajamos script-src ('unsafe-eval') y connect-src
    // (ws:) para no romper el Hot Module Replacement.
    const scriptSrc = isDev
      ? "'self' 'unsafe-inline' 'unsafe-eval'"
      : "'self' 'unsafe-inline'";
    const connectSrc = isDev
      ? "'self' ws: wss: https://*.trycloudflare.com"
      : "'self' https://*.trycloudflare.com";

    const csp = [
      "default-src 'self'",
      "base-uri 'self'",
      "object-src 'none'",
      "frame-ancestors 'none'",
      "form-action 'self'",
      "img-src 'self' data: blob:",
      "font-src 'self' data:",
      `script-src ${scriptSrc}`,
      "style-src 'self' 'unsafe-inline'",
      `connect-src ${connectSrc}`,
    ].join("; ");

    return [
      {
        source: "/:path*",
        headers: [
          { key: "Content-Security-Policy", value: csp },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        ],
      },
    ];
  },

  async rewrites() {
    const backend = process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8000";
    console.log("[next.config] rewrites() backend =", backend);
    return [
      {
        source: "/backend/:path*",
        destination: `${backend}/:path*`,
      },
    ];
  },
};

export default nextConfig;