"""Operational lifespan-only health routes."""

from __future__ import annotations

from fastapi import APIRouter, Request, Response

router = APIRouter()


@router.get("/health/live", response_model=None)
async def live(request: Request) -> Response | dict[str, str]:
    if not request.app.state.runtime.live:
        return Response(
            status_code=503, content='{"status":"unavailable"}', media_type="application/json"
        )
    return {"status": "live"}


@router.get("/health/ready", response_model=None)
async def ready(request: Request) -> Response | dict[str, str]:
    if not request.app.state.runtime.ready:
        return Response(
            status_code=503, content='{"status":"unavailable"}', media_type="application/json"
        )
    return {"status": "ready"}
