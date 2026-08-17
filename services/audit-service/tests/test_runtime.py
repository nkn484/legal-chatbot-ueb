"""Unit and in-process ASGI integration tests for the audit runtime template sample."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import unittest
from io import StringIO
from pathlib import Path
from typing import Any
from unittest.mock import patch

import httpx
from fastapi import HTTPException
from pydantic import ValidationError

SERVICE_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = SERVICE_ROOT.parents[1]
sys.path.insert(0, str(SERVICE_ROOT / "src"))

from audit_service.app import create_app  # noqa: E402
from audit_service.context import (  # noqa: E402
    bounded_identifier,
    correlation_id_var,
    request_id_var,
    trace_id_from_traceparent,
    trace_id_var,
)
from audit_service.logging import JsonFormatter, configure_logging  # noqa: E402
from audit_service.middleware import (  # noqa: E402
    RequestContextMiddleware,
    SanitizedErrorMiddleware,
)
from audit_service.migrations import MigrationCompatibility  # noqa: E402
from audit_service.settings import Settings  # noqa: E402

CANARY = "audit-runtime-secret-canary-7f4b"


def make_settings(**overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "environment": "test",
        "instance_id": "audit-test-1",
        "http_connect_timeout_seconds": 1.0,
        "http_read_timeout_seconds": 2.0,
        "http_write_timeout_seconds": 3.0,
        "http_pool_timeout_seconds": 4.0,
        "http_max_connections": 10,
        "http_max_keepalive_connections": 5,
    }
    values.update(overrides)
    return Settings(**values)


def captured_logging(buffer: StringIO) -> Any:
    def configure(settings: Settings) -> logging.Logger:
        logger = configure_logging(settings)
        handler = logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        handler.setStream(buffer)
        return logger

    return configure


def log_records(buffer: StringIO) -> list[dict[str, Any]]:
    return [json.loads(line) for line in buffer.getvalue().splitlines() if line]


class SettingsTests(unittest.TestCase):
    def test_missing_invalid_and_extra_settings_fail_fast(self) -> None:
        audit_environment = os.environ.pop("AUDIT_ENVIRONMENT", None)
        try:
            with self.assertRaises(ValidationError):
                Settings()  # type: ignore[call-arg]
        finally:
            if audit_environment is not None:
                os.environ["AUDIT_ENVIRONMENT"] = audit_environment
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValidationError):
            create_app()
        with self.assertRaises(ValidationError):
            make_settings(http_connect_timeout_seconds=0)
        with self.assertRaises(ValidationError):
            values: dict[str, Any] = {
                "environment": "test",
                "instance_id": "audit-test-1",
                "http_connect_timeout_seconds": 1.0,
                "http_read_timeout_seconds": 2.0,
                "http_write_timeout_seconds": 3.0,
                "http_pool_timeout_seconds": 4.0,
                "http_max_connections": 10,
                "http_max_keepalive_connections": 5,
                "unexpected": "value",
            }
            Settings(**values)

    def test_settings_are_not_implicitly_constructed_at_import(self) -> None:
        self.assertEqual(Settings.service_name, "audit-service")
        self.assertEqual(Settings.service_version, "0.1.0")


class RuntimeIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def request(
        self,
        app: Any,
        path: str,
        headers: dict[str, str] | None = None,
        method: str = "GET",
        content: str | None = None,
    ) -> httpx.Response:
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://audit.test") as client:
            return await client.request(method, path, headers=headers, content=content)

    async def test_health_lifecycle_client_and_teardown(self) -> None:
        app = create_app(make_settings())
        before_live = await self.request(app, "/health/live")
        before_ready = await self.request(app, "/health/ready")
        self.assertEqual((before_live.status_code, before_ready.status_code), (503, 503))

        async with app.router.lifespan_context(app):
            self.assertTrue(app.state.runtime.live)
            self.assertTrue(app.state.runtime.ready)
            configuration = app.state.runtime.client_configuration
            self.assertIsNotNone(configuration)
            assert configuration is not None
            self.assertEqual(configuration.connect_timeout_seconds, 1.0)
            self.assertEqual(configuration.read_timeout_seconds, 2.0)
            self.assertEqual(configuration.write_timeout_seconds, 3.0)
            self.assertEqual(configuration.pool_timeout_seconds, 4.0)
            self.assertEqual(configuration.max_connections, 10)
            self.assertEqual(configuration.max_keepalive_connections, 5)
            self.assertFalse(configuration.follow_redirects)
            live = await self.request(app, "/health/live")
            ready = await self.request(app, "/health/ready")
            self.assertEqual((live.status_code, ready.status_code), (200, 200))
            self.assertEqual((live.json(), ready.json()), ({"status": "live"}, {"status": "ready"}))

        self.assertFalse(app.state.runtime.live)
        self.assertFalse(app.state.runtime.ready)
        self.assertTrue(app.state.runtime.client_closed)
        assert app.state.runtime.client is not None
        self.assertTrue(app.state.runtime.client.is_closed)

    async def test_migration_startup_failure_closes_client_and_never_becomes_ready(self) -> None:
        async def failed_hook() -> MigrationCompatibility:
            raise RuntimeError(CANARY)

        buffer = StringIO()
        app = create_app(
            make_settings(), migration_hook=failed_hook, logging_configurer=captured_logging(buffer)
        )
        with self.assertRaisesRegex(RuntimeError, "startup compatibility check failed") as raised:
            async with app.router.lifespan_context(app):
                self.fail("failed migration hook must not yield")
        self.assertNotIn(CANARY, str(raised.exception))
        self.assertFalse(app.state.runtime.live)
        self.assertFalse(app.state.runtime.ready)
        self.assertTrue(app.state.runtime.client_closed)
        records = log_records(buffer)
        self.assertIn("startup_failed", [record["event"] for record in records])
        self.assertEqual(
            next(record for record in records if record["event"] == "startup_failed")["error_type"],
            "RuntimeError",
        )
        self.assertEqual(
            next(record for record in records if record["event"] == "startup_failed")["level"],
            "ERROR",
        )
        self.assertNotIn(CANARY, buffer.getvalue())

    async def test_client_factory_startup_failure_is_sanitized_and_finalized(self) -> None:
        def failed_client_factory(_: Settings) -> httpx.AsyncClient:
            raise RuntimeError(CANARY)

        buffer = StringIO()
        app = create_app(
            make_settings(),
            logging_configurer=captured_logging(buffer),
            http_client_factory=failed_client_factory,
        )
        with self.assertRaisesRegex(RuntimeError, "startup compatibility check failed") as raised:
            async with app.router.lifespan_context(app):
                self.fail("failed client factory must not yield")
        self.assertNotIn(CANARY, str(raised.exception))
        self.assertIsNone(app.state.runtime.client)
        self.assertFalse(app.state.runtime.live)
        self.assertFalse(app.state.runtime.ready)
        assert app.state.runtime.logger is not None
        self.assertEqual(app.state.runtime.logger.handlers, [])
        records = log_records(buffer)
        self.assertEqual(
            [
                (record["event"], record["level"], record["error_type"])
                for record in records
                if record["event"] == "startup_failed"
            ],
            [("startup_failed", "ERROR", "RuntimeError")],
        )
        self.assertNotIn(CANARY, buffer.getvalue())

    async def test_liveness_precedes_blocked_migration_and_repeated_lifespans_close_clients(
        self,
    ) -> None:
        entered = asyncio.Event()
        release = asyncio.Event()

        async def blocked_hook() -> MigrationCompatibility:
            entered.set()
            await release.wait()
            return MigrationCompatibility.READY

        buffer = StringIO()
        app = create_app(
            make_settings(),
            migration_hook=blocked_hook,
            logging_configurer=captured_logging(buffer),
        )

        async def enter_lifespan() -> None:
            async with app.router.lifespan_context(app):
                pass

        task = asyncio.create_task(enter_lifespan())
        await entered.wait()
        self.assertTrue(app.state.runtime.live)
        self.assertFalse(app.state.runtime.ready)
        release.set()
        await task
        self.assertFalse(app.state.runtime.live)
        self.assertFalse(app.state.runtime.ready)

        class CountingClient(httpx.AsyncClient):
            def __init__(self) -> None:
                super().__init__()
                self.close_calls = 0

            async def aclose(self) -> None:
                self.close_calls += 1
                await super().aclose()

        clients: list[CountingClient] = []

        def make_counting_client(_: Settings) -> CountingClient:
            client = CountingClient()
            clients.append(client)
            return client

        repeat_buffer = StringIO()
        repeat_app = create_app(
            make_settings(),
            logging_configurer=captured_logging(repeat_buffer),
            http_client_factory=make_counting_client,
        )
        for _ in range(2):
            async with repeat_app.router.lifespan_context(repeat_app):
                client = repeat_app.state.runtime.client
                self.assertIsNotNone(client)
                assert repeat_app.state.runtime.logger is not None
                self.assertEqual(len(repeat_app.state.runtime.logger.handlers), 1)
            self.assertTrue(repeat_app.state.runtime.client_closed)
            assert repeat_app.state.runtime.logger is not None
            self.assertEqual(repeat_app.state.runtime.logger.handlers, [])
        self.assertIsNot(clients[0], clients[1])
        self.assertTrue(all(client.is_closed and client.close_calls == 1 for client in clients))

    async def test_problem_responses_context_headers_and_context_reset(self) -> None:
        buffer = StringIO()
        app = create_app(make_settings(), logging_configurer=captured_logging(buffer))

        @app.get("/test-http")
        async def test_http() -> None:
            raise HTTPException(status_code=418, detail=CANARY)

        @app.get("/test-boom")
        async def test_boom() -> None:
            raise RuntimeError(CANARY)

        @app.get("/test-validation/{value}")
        async def test_validation(value: int) -> dict[str, int]:
            return {"value": value}

        async with app.router.lifespan_context(app):
            valid_headers = {
                "x-request-id": "request-123",
                "x-correlation-id": "correlation-123",
                "traceparent": "00-0123456789abcdef0123456789abcdef-0123456789abcdef-01",
            }
            sensitive_headers = {**valid_headers, "authorization": CANARY, "cookie": CANARY}
            http_error = await self.request(
                app, f"/test-http?untrusted={CANARY}", sensitive_headers
            )
            unexpected_error = await self.request(app, "/test-boom", valid_headers)
            validation_error = await self.request(app, "/test-validation/not-an-int", valid_headers)
            not_found = await self.request(app, "/missing", valid_headers)
            body_error = await self.request(
                app,
                "/health/live",
                sensitive_headers,
                method="POST",
                content=CANARY,
            )
            for response, status, code in (
                (http_error, 418, "http_error"),
                (unexpected_error, 500, "internal_error"),
                (validation_error, 422, "validation_error"),
                (not_found, 404, "http_error"),
                (body_error, 405, "http_error"),
            ):
                self.assertEqual(response.status_code, status)
                self.assertEqual(response.headers["content-type"], "application/problem+json")
                self.assertEqual(response.headers["cache-control"], "no-store")
                self.assertEqual(response.headers["x-request-id"], "request-123")
                self.assertEqual(response.headers["x-correlation-id"], "correlation-123")
                self.assertEqual(response.json()["code"], code)
                self.assertNotIn(CANARY, response.text)

            invalid_ids = await self.request(
                app,
                "/health/live",
                {"x-request-id": "not valid!", "x-correlation-id": "x" * 65, "traceparent": "bad"},
            )
            self.assertEqual(invalid_ids.status_code, 200)
            self.assertRegex(invalid_ids.headers["x-request-id"], r"^[a-f0-9]{32}$")
            self.assertRegex(invalid_ids.headers["x-correlation-id"], r"^[a-f0-9]{32}$")
        records = log_records(buffer)
        completed = [record for record in records if record["event"] == "request_completed"]
        failed = [record for record in records if record["event"] == "request_failed"]
        self.assertTrue(completed)
        self.assertTrue(failed)
        for record in completed + failed:
            self.assertEqual(record["service"], "audit-service")
            self.assertEqual(record["environment"], "test")
            self.assertEqual(record["instance_id"], "audit-test-1")
            self.assertIn("status", record)
            self.assertRegex(
                record["timestamp"],
                r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$",
            )
        self.assertTrue(all(record["level"] == "INFO" for record in completed))
        self.assertTrue(all(record["level"] == "ERROR" for record in failed))
        self.assertIn("request-123", [record["request_id"] for record in completed])
        self.assertIn("request-123", [record["request_id"] for record in failed])
        self.assertIn("/test-http", [record["route"] for record in completed])
        self.assertNotIn(CANARY, buffer.getvalue())
        self.assertIsNone(request_id_var.get())
        self.assertIsNone(correlation_id_var.get())
        self.assertIsNone(trace_id_var.get())


class SafetyAndTemplateTests(unittest.TestCase):
    def test_identifier_trace_validation_and_json_redaction(self) -> None:
        self.assertEqual(bounded_identifier("valid-id_1"), "valid-id_1")
        self.assertRegex(bounded_identifier("invalid value"), r"^[a-f0-9]{32}$")
        valid_trace = "0123456789abcdef0123456789abcdef"
        self.assertEqual(
            trace_id_from_traceparent(f"00-{valid_trace}-0123456789abcdef-01"), valid_trace
        )
        self.assertRegex(trace_id_from_traceparent("00-bad"), r"^[a-f0-9]{32}$")
        self.assertRegex(
            trace_id_from_traceparent("00-0123456789abcdef0123456789abcdef-0000000000000000-01"),
            r"^[a-f0-9]{32}$",
        )
        record = logging.LogRecord("audit_service", logging.INFO, "", 0, CANARY, (), None)
        record.structured_fields = {
            "event": "test",
            "level": "CALLER_CONTROLLED",
            "details": {"nested": [{"api_key": CANARY}], "cookie": CANARY},
        }
        output = JsonFormatter(make_settings()).format(record)
        parsed = json.loads(output)
        self.assertEqual(parsed["details"]["nested"][0]["api_key"], "[REDACTED]")
        self.assertEqual(parsed["details"]["cookie"], "[REDACTED]")
        self.assertEqual(parsed["level"], "INFO")
        self.assertRegex(parsed["timestamp"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
        self.assertNotIn(CANARY, output)

    def test_response_start_failure_never_sends_a_second_start_or_leaks(self) -> None:
        messages: list[Any] = []
        buffer = StringIO()
        app = create_app(make_settings(), logging_configurer=captured_logging(buffer))

        async def started_then_failed(_: Any, __: Any, send: Any) -> None:
            await send({"type": "http.response.start", "status": 200, "headers": []})
            raise RuntimeError(CANARY)

        async def receive() -> Any:
            return {"type": "http.disconnect"}

        async def send(message: Any) -> None:
            messages.append(message)

        async def run() -> None:
            wrapped = RequestContextMiddleware(SanitizedErrorMiddleware(started_then_failed))
            async with app.router.lifespan_context(app):
                scope: dict[str, Any] = {
                    "type": "http",
                    "method": "GET",
                    "headers": [],
                    "app": app,
                }
                await wrapped(scope, receive, send)

        asyncio.run(run())
        self.assertEqual([message["type"] for message in messages].count("http.response.start"), 1)
        self.assertEqual(
            messages[-1], {"type": "http.response.body", "body": b"", "more_body": False}
        )
        self.assertNotIn(CANARY, repr(messages))
        self.assertNotIn(CANARY, buffer.getvalue())
        self.assertIn("request_failed", [record["event"] for record in log_records(buffer)])

    def test_template_parity_and_no_cross_service_runtime_imports(self) -> None:
        template_root = (
            REPOSITORY_ROOT / "packages" / "workspace-tooling" / "templates" / "fastapi-service"
        )
        substitutions = {
            "{{SERVICE_NAME}}": "audit-service",
            "{{MODULE_NAME}}": "audit_service",
            "{{ENV_PREFIX}}": "AUDIT_",
        }
        for template in sorted((template_root / "src" / "template_service").glob("*.py")):
            rendered = template.read_text(encoding="utf-8")
            for token, value in substitutions.items():
                rendered = rendered.replace(token, value)
            actual = SERVICE_ROOT / "src" / "audit_service" / template.name
            self.assertEqual(actual.read_text(encoding="utf-8"), rendered, msg=template.name)
        for template_name, actual_name in {
            "README.md.template": "README.md",
            "pyproject.toml.template": "pyproject.toml",
            "requirements.in.template": "requirements.in",
            "requirements-dev.in.template": "requirements-dev.in",
            ".gitignore.template": ".gitignore",
        }.items():
            rendered = (template_root / template_name).read_text(encoding="utf-8")
            for token, value in substitutions.items():
                rendered = rendered.replace(token, value)
            self.assertEqual((SERVICE_ROOT / actual_name).read_text(encoding="utf-8"), rendered)
        self.assertFalse((template_root / "requirements.txt.template").exists())
        self.assertFalse((template_root / "requirements-dev.txt.template").exists())
        source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (SERVICE_ROOT / "src" / "audit_service").glob("*.py")
        )
        self.assertNotIn("workspace_tooling", source)
        self.assertNotIn("services.", source)
        self.assertNotIn("sqlalchemy", source)


if __name__ == "__main__":
    unittest.main()
