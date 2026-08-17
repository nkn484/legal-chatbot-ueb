"""App factory and asynchronous lifecycle for {{SERVICE_NAME}}."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass

import httpx
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .health import router as health_router
from .http_client import HttpClientConfiguration, client_configuration, create_http_client
from .logging import EventSeverity, close_logging, configure_logging, emit
from .middleware import (
    RequestContextMiddleware,
    SanitizedErrorMiddleware,
    http_exception_handler,
    validation_exception_handler,
)
from .migrations import MigrationCompatibility, read_only_migration_compatibility
from .settings import Settings

MigrationHook = Callable[[], Awaitable[MigrationCompatibility]]
LoggingConfigurer = Callable[[Settings], logging.Logger]
HttpClientFactory = Callable[[Settings], httpx.AsyncClient]


@dataclass
class RuntimeState:
    live: bool = False
    ready: bool = False
    client: httpx.AsyncClient | None = None
    client_closed: bool = False
    client_configuration: HttpClientConfiguration | None = None
    logger: logging.Logger | None = None


def create_app(
    settings: Settings | None = None,
    migration_hook: MigrationHook = read_only_migration_compatibility,
    logging_configurer: LoggingConfigurer = configure_logging,
    http_client_factory: HttpClientFactory = create_http_client,
) -> FastAPI:
    """Create a configured application without I/O or a global settings instance."""
    active_settings = settings if settings is not None else Settings()  # type: ignore[call-arg]
    runtime = RuntimeState()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        runtime.client = None
        runtime.client_configuration = None
        runtime.client_closed = False
        runtime.ready = False
        runtime.live = False
        runtime.logger = None
        logger: logging.Logger | None = None
        try:
            try:
                logger = logging_configurer(active_settings)
                runtime.logger = logger
                runtime.client_configuration = client_configuration(active_settings)
                runtime.client = http_client_factory(active_settings)
                runtime.live = True
                compatibility = await migration_hook()
                if compatibility not in {
                    MigrationCompatibility.READY,
                    MigrationCompatibility.NOT_APPLICABLE,
                }:
                    raise RuntimeError("migration compatibility gate failed")
            except Exception as error:  # noqa: BLE001
                if logger is not None:
                    emit(
                        logger,
                        "startup_failed",
                        severity=EventSeverity.ERROR,
                        error_type=type(error).__name__,
                    )
                raise RuntimeError("startup compatibility check failed") from None
            runtime.ready = True
            assert logger is not None
            emit(logger, "lifespan_started")
            yield
        finally:
            runtime.ready = False
            runtime.live = False
            if runtime.client is not None and not runtime.client_closed:
                await runtime.client.aclose()
                runtime.client_closed = True
            if logger is not None:
                emit(logger, "lifespan_stopped")
                close_logging(logger)

    app = FastAPI(title=Settings.service_name, version=Settings.service_version, lifespan=lifespan)
    app.state.runtime = runtime
    app.add_middleware(SanitizedErrorMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.include_router(health_router)
    return app
