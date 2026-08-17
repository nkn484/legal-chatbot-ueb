"""Pure-ASGI request context and sanitized problem response middleware."""

from __future__ import annotations

import logging
from http import HTTPStatus
from time import perf_counter

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .context import (
    RequestContext,
    bounded_identifier,
    request_id_var,
    reset_context,
    set_context,
    trace_id_from_traceparent,
)
from .logging import EventSeverity, emit

_ALLOWED_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"})


def _safe_method(value: object) -> str:
    return value if isinstance(value, str) and value in _ALLOWED_METHODS else "UNKNOWN"


def _safe_route(value: object) -> str:
    if isinstance(value, str) and value.startswith("/") and "?" not in value and len(value) <= 128:
        return value
    return "unmatched"


def _safe_error_type(error: BaseException) -> str:
    name = type(error).__name__
    return name if name.isidentifier() and len(name) <= 64 else "Exception"


def problem_response(status: int, title: str, code: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "type": "about:blank",
            "title": title,
            "status": status,
            "code": code,
            "request_id": request_id_var.get() or "unknown",
        },
        media_type="application/problem+json",
        headers={"Cache-Control": "no-store"},
    )


class RequestContextMiddleware:
    """Pure ASGI middleware that injects validated identifiers and resets ContextVars."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope["headers"]
        }
        context = RequestContext(
            request_id=bounded_identifier(headers.get("x-request-id")),
            correlation_id=bounded_identifier(headers.get("x-correlation-id")),
            trace_id=trace_id_from_traceparent(headers.get("traceparent")),
        )
        tokens = set_context(context)
        started_at = perf_counter()
        response_status = 500
        response_completed = False

        async def send_with_context(message: Message) -> None:
            nonlocal response_completed, response_status
            if message["type"] == "http.response.start":
                response_status = int(message["status"])
                response_headers = list(message.get("headers", []))
                response_headers.extend(
                    [
                        (b"x-request-id", context.request_id.encode("ascii")),
                        (b"x-correlation-id", context.correlation_id.encode("ascii")),
                    ]
                )
                message = {**message, "headers": response_headers}
            elif message["type"] == "http.response.body" and not message.get("more_body", False):
                response_completed = True
            await send(message)

        try:
            await self.app(scope, receive, send_with_context)
        finally:
            route = scope.get("route")
            route_template = getattr(route, "path", "unmatched")
            duration_ms = min(60_000, max(0, round((perf_counter() - started_at) * 1000)))
            emit(
                _scope_logger(scope),
                "request_completed",
                method=_safe_method(scope.get("method")),
                route=_safe_route(route_template),
                status=response_status,
                duration_ms=duration_ms,
            )
            reset_context(tokens)


class SanitizedErrorMiddleware:
    """Pure ASGI last-resort exception conversion preserving request context identifiers."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        response_started = False
        response_completed = False

        async def tracked_send(message: Message) -> None:
            nonlocal response_completed, response_started
            if message["type"] == "http.response.start":
                response_started = True
            elif message["type"] == "http.response.body" and not message.get("more_body", False):
                response_completed = True
            await send(message)

        try:
            await self.app(scope, receive, tracked_send)
        except Exception as error:  # noqa: BLE001
            emit(
                _scope_logger(scope),
                "request_failed",
                severity=EventSeverity.ERROR,
                status=500,
                error_type=_safe_error_type(error),
            )
            if not response_started:
                response = problem_response(500, "Internal Server Error", "internal_error")
                await response(scope, receive, tracked_send)
            elif not response_completed:
                await tracked_send({"type": "http.response.body", "body": b"", "more_body": False})


def _scope_logger(scope: Scope) -> logging.Logger:
    app = scope.get("app")
    runtime = getattr(getattr(app, "state", None), "runtime", None)
    logger = getattr(runtime, "logger", None)
    return logger if isinstance(logger, logging.Logger) else logging.getLogger("{{MODULE_NAME}}")


async def validation_exception_handler(_: Request, __: RequestValidationError) -> JSONResponse:
    return problem_response(422, "Validation failed", "validation_error")


async def http_exception_handler(_: Request, error: StarletteHTTPException) -> JSONResponse:
    status = error.status_code
    title = HTTPStatus(status).phrase if status in HTTPStatus._value2member_map_ else "HTTP error"
    return problem_response(status, title, "http_error")
