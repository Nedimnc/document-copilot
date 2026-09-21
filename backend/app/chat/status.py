"""Pipeline status events for the AI SDK UI message stream."""

from __future__ import annotations

from typing import Any, Literal

PipelinePhase = Literal["retrieval", "generating", "validating", "refusal", "done"]


def status_event(*, phase: PipelinePhase, label: str) -> dict[str, Any]:
    return {
        "type": "data-copilot-status",
        "data": {"phase": phase, "label": label},
    }
