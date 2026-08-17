"""Request-scoped identifiers with ContextVar reset guarantees."""

from __future__ import annotations

import re
import uuid
from contextvars import ContextVar, Token
from dataclasses import dataclass

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)
trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)

_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_TRACEPARENT = re.compile(
    r"^(?P<version>[0-9a-f]{2})-(?P<trace>[0-9a-f]{32})-(?P<parent>[0-9a-f]{16})-(?P<flags>[0-9a-f]{2})$"
)


@dataclass(frozen=True)
class RequestContext:
    request_id: str
    correlation_id: str
    trace_id: str


def bounded_identifier(value: str | None) -> str:
    if value is not None and _IDENTIFIER.fullmatch(value):
        return value
    return uuid.uuid4().hex


def trace_id_from_traceparent(value: str | None) -> str:
    if value is not None:
        match = _TRACEPARENT.fullmatch(value)
        if (
            match is not None
            and match.group("version") != "ff"
            and set(match.group("trace")) != {"0"}
            and set(match.group("parent")) != {"0"}
        ):
            return match.group("trace")
    return uuid.uuid4().hex


def set_context(
    context: RequestContext,
) -> tuple[Token[str | None], Token[str | None], Token[str | None]]:
    return (
        request_id_var.set(context.request_id),
        correlation_id_var.set(context.correlation_id),
        trace_id_var.set(context.trace_id),
    )


def reset_context(tokens: tuple[Token[str | None], Token[str | None], Token[str | None]]) -> None:
    request_id_var.reset(tokens[0])
    correlation_id_var.reset(tokens[1])
    trace_id_var.reset(tokens[2])
