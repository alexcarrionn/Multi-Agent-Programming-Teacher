"""Rate limiting con slowapi (port de Flask-Limiter para Starlette/FastAPI).

Estrategia de clave "usuario-o-IP":
  - Si la peticion trae un JWT valido en la cookie `access_token`, se limita por
    IDENTIDAD de usuario (`user:{rol}:{id}`): asi un mismo usuario comparte cubo
    aunque cambie de IP o abra varias pestañas.
  - Si no hay sesion, se limita por IP REAL del cliente.

Por que la IP real necesita cuidado:
  En produccion la cadena es  navegador -> Cloudflare -> nginx -> api:8000.
  Por tanto `request.client.host` es la IP del contenedor nginx y seria
  COMPARTIDA por todos los usuarios (un solo usuario activo bloquearia a todos).
  nginx nos pasa la IP real en `X-Real-IP` (ver nginx/default.conf.template).
  Nos fiamos de `X-Real-IP` (la pone el proxy) antes que del `X-Forwarded-For`
  crudo, que el cliente puede falsear para rotar de cubo y saltarse el limite.
"""
from jose import JWTError, jwt
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from config.settings import settings


def get_client_ip(request: Request) -> str:
    """IP real del cliente teniendo en cuenta el proxy (nginx)."""
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # El primer valor de la lista es el cliente original.
        return forwarded.split(",")[0].strip()
    # Sin proxy delante (dev local): IP del socket.
    return get_remote_address(request)


def user_or_ip_key(request: Request) -> str:
    """Clave de limitacion: por usuario si esta autenticado, si no por IP."""
    token = request.cookies.get("access_token")
    if token:
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
            rol = payload.get("rol", "user")
            uid = (
                payload.get("alumno_id")
                or payload.get("docente_id")
                or payload.get("sub")
            )
            if uid is not None:
                return f"user:{rol}:{uid}"
        except JWTError:
            # Token invalido/expirado: caemos a limitar por IP.
            pass
    return f"ip:{get_client_ip(request)}"


# Instancia unica del limitador. `default_limits` se aplica a TODAS las rutas a
# traves de SlowAPIMiddleware (ver main.py). `headers_enabled` añade las cabeceras
# X-RateLimit-* a las respuestas para que el cliente sepa cuanto le queda.
limiter = Limiter(
    key_func=user_or_ip_key,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
    storage_uri=settings.RATE_LIMIT_STORAGE,
    headers_enabled=True,
    enabled=settings.RATE_LIMIT_ENABLED,
)
