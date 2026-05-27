"""Lightweight execution tracing (OpenTelemetry-ready shape)."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TraceSpan:
    name: str
    start_ms: float
    end_ms: float | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    status: str = "ok"

    @property
    def duration_ms(self) -> float | None:
        if self.end_ms is None:
            return None
        return self.end_ms - self.start_ms


class Tracer:
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self.trace_id = str(uuid.uuid4())
        self.spans: list[TraceSpan] = []

    def start_span(self, name: str, **attributes: Any) -> TraceSpan:
        span = TraceSpan(name=name, start_ms=time.time() * 1000, attributes=dict(attributes))
        if self.enabled:
            self.spans.append(span)
        return span

    def end_span(self, span: TraceSpan, status: str = "ok", **attributes: Any) -> None:
        span.end_ms = time.time() * 1000
        span.status = status
        span.attributes.update(attributes)

    def summary(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for span in self.spans:
            out.append(
                {
                    "name": span.name,
                    "duration_ms": span.duration_ms,
                    "status": span.status,
                    "attributes": span.attributes,
                }
            )
        return out
