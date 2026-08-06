"""Shared `/availability` response shape for modules gated behind a
`check_available()` capability check (Fine-Tuning, Image Generation, Video
Generation) — each has its own dependency set and failure message, but the
same "call the gate, report the result" endpoint shape."""

from collections.abc import Callable

from pydantic import BaseModel


class AvailabilityResponse(BaseModel):
    available: bool
    reason: str | None = None


def check_availability(check: Callable[[], None]) -> AvailabilityResponse:
    try:
        check()
        return AvailabilityResponse(available=True)
    except RuntimeError as exc:
        return AvailabilityResponse(available=False, reason=str(exc))
