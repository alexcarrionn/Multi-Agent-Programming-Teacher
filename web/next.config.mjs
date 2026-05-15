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