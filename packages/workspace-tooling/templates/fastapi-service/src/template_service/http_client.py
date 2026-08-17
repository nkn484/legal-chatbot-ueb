"""Service-local outbound client factory; construction does not perform I/O."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from .settings import Settings


@dataclass(frozen=True)
class HttpClientConfiguration:
    """Owned, inspectable client constraints without exposing HTTPX internals."""

    connect_timeout_seconds: float
    read_timeout_seconds: float
    write_timeout_seconds: float
    pool_timeout_seconds: float
    max_connections: int
    max_keepalive_connections: int
    follow_redirects: bool = False


def client_configuration(settings: Settings) -> HttpClientConfiguration:
    return HttpClientConfiguration(
        connect_timeout_seconds=settings.http_connect_timeout_seconds,
        read_timeout_seconds=settings.http_read_timeout_seconds,
        write_timeout_seconds=settings.http_write_timeout_seconds,
        pool_timeout_seconds=settings.http_pool_timeout_seconds,
        max_connections=settings.http_max_connections,
        max_keepalive_connections=settings.http_max_keepalive_connections,
    )


def create_http_client(settings: Settings) -> httpx.AsyncClient:
    configuration = client_configuration(settings)
    timeout = httpx.Timeout(
        connect=configuration.connect_timeout_seconds,
        read=configuration.read_timeout_seconds,
        write=configuration.write_timeout_seconds,
        pool=configuration.pool_timeout_seconds,
    )
    limits = httpx.Limits(
        max_connections=configuration.max_connections,
        max_keepalive_connections=configuration.max_keepalive_connections,
    )
    return httpx.AsyncClient(
        timeout=timeout,
        limits=limits,
        follow_redirects=configuration.follow_redirects,
    )
