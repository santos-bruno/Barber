"""Camada de segurança da API: headers HTTP, limite de tamanho de corpo e
rate limiting (proteção contra força bruta e spam).

Tudo em memória — a API roda em processo único (plano free do Render). Se um dia
escalar para vários workers/instâncias, troque o RateLimiter por Redis para que o
limite seja compartilhado.
"""
import os
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

# Tamanho máximo do corpo da requisição (evita payloads gigantes / DoS).
MAX_BODY_BYTES = int(os.getenv("MAX_BODY_BYTES", str(1_000_000)))  # 1 MB


def client_ip(request: Request) -> str:
    """IP real do cliente (respeita o X-Forwarded-For do proxy do Render)."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "0.0.0.0"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adiciona cabeçalhos de segurança e barra corpos grandes cedo."""

    async def dispatch(self, request: Request, call_next):
        cl = request.headers.get("content-length")
        if cl and cl.isdigit() and int(cl) > MAX_BODY_BYTES:
            return JSONResponse(
                {"detail": "Requisição muito grande."},
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        response: Response = await call_next(request)

        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'self'",
        )
        # HSTS só sob HTTPS (o Render serve HTTPS na frente).
        if (
            request.url.scheme == "https"
            or request.headers.get("x-forwarded-proto") == "https"
        ):
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response


class _RateLimiter:
    """Janela deslizante por (bucket, ip), em memória e thread-safe."""

    def __init__(self) -> None:
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()
        self._last_gc = time.time()

    def allow(self, key: str, limit: int, window: int) -> bool:
        now = time.time()
        with self._lock:
            dq = self._hits[key]
            while dq and dq[0] <= now - window:
                dq.popleft()
            if len(dq) >= limit:
                return False
            dq.append(now)
            # Limpeza esporádica de chaves ociosas (evita crescer sem parar).
            if now - self._last_gc > 300:
                self._gc(now)
                self._last_gc = now
            return True

    def _gc(self, now: float) -> None:
        for k in list(self._hits.keys()):
            dq = self._hits[k]
            if not dq or dq[-1] <= now - 3600:
                self._hits.pop(k, None)


_limiter = _RateLimiter()


def rate_limit(bucket: str, limit: int, window: int = 60):
    """Fábrica de dependência do FastAPI que limita requisições por IP.

    Ex.: `dependencies=[Depends(rate_limit("login", 12, 60))]` → no máx. 12
    requisições por minuto por IP naquele endpoint.
    """

    def _dep(request: Request) -> None:
        ip = client_ip(request)
        if not _limiter.allow(f"{bucket}:{ip}", limit, window):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitas tentativas. Aguarde um momento e tente novamente.",
            )

    return _dep
