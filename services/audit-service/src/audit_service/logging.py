"""Allowlisted JSON logging with recursive sensitive-key redaction."""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from datetime import UTC, datetime
from enum import IntEnum
from typing import Any

from .context import correlation_id_var, request_id_var, trace_id_var
from .settings import Settings

_REDACTED = "[REDACTED]"
_SENSITIVE_PARTS = (
    "authorization",
    "cookie",
    "password",
    "secret",
    "token",
    "apikey",
    "credential",
    "dsn",
)
_ALLOWED_FIELDS = frozenset(
    {"event", "status", "error_type", "method", "route", "duration_ms", "details"}
)


class EventSeverity(IntEnum):
    """Internal event severities; payload severity is never caller-controlled."""

    INFO = logging.INFO
    ERROR = logging.ERROR


def is_sensitive_key(key: object) -> bool:
    normalized = "".join(character for character in str(key).lower() if character.isalnum())
    return any(part in normalized for part in _SENSITIVE_PARTS)


def redact(value: Any, key: object | None = None) -> Any:
    if key is not None and is_sensitive_key(key):
        return _REDACTED
    if isinstance(value, Mapping):
        return {
            str(item_key): redact(item_value, item_key) for item_key, item_value in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return [redact(item) for item in value]
    return value


class JsonFormatter(logging.Formatter):
    """Formats only allowlisted structured fields; never formats raw log messages."""

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._service = settings.service_name
        self._version = settings.service_version
        self._environment = settings.environment
        self._instance_id = settings.instance_id

    def format(self, record: logging.LogRecord) -> str:
        supplied = getattr(record, "structured_fields", {})
        fields = supplied if isinstance(supplied, Mapping) else {}
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "service": self._service,
            "version": self._version,
            "environment": self._environment,
            "instance_id": self._instance_id,
            "level": record.levelname,
            "request_id": request_id_var.get(),
            "correlation_id": correlation_id_var.get(),
            "trace_id": trace_id_var.get(),
        }
        for key in _ALLOWED_FIELDS:
            if key in fields:
                payload[key] = redact(fields[key], key)
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def configure_logging(settings: Settings) -> logging.Logger:
    """Install one owned JSON handler, closing prior owned handlers deterministically."""
    logger = logging.getLogger("audit_service")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    close_logging(logger)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter(settings))
    logger.addHandler(handler)
    return logger


def close_logging(logger: logging.Logger) -> None:
    """Flush and close only this service's handlers without touching global logging."""
    for handler in list(logger.handlers):
        handler.flush()
        handler.close()
        logger.removeHandler(handler)


def emit(
    logger: logging.Logger,
    event: str,
    *,
    severity: EventSeverity = EventSeverity.INFO,
    **fields: Any,
) -> None:
    """Emit an allowlisted event without formatting a raw message."""
    structured_fields = {"event": event}
    structured_fields.update(
        {key: value for key, value in fields.items() if key in _ALLOWED_FIELDS}
    )
    logger.log(int(severity), "", extra={"structured_fields": structured_fields})
