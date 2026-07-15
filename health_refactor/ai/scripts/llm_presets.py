"""Shared structured-extraction presets for manual LLM test scripts."""
from __future__ import annotations

from dataclasses import dataclass

from ai.src.domain.llm.prompt_templates import (
    CLASSIFICATION_EXTRACTION_SYSTEM,
    ORDER_EXTRACTION_SYSTEM,
    TICKET_EXTRACTION_SYSTEM,
)


@dataclass(frozen=True)
class StructuredExtractionPreset:
    format_file: str
    system: str
    prompt: str


STRUCTURED_PRESETS: dict[str, StructuredExtractionPreset] = {
    "order": StructuredExtractionPreset(
        format_file="ai/scripts/fixtures/order_json_format.json",
        system=ORDER_EXTRACTION_SYSTEM,
        prompt=(
            "From: ada@acme.com\n\n"
            "Process for Acme Corp: 1x Widget Pro (id W-100), 2x Gadget Mini (id G-200)."
        ),
    ),
    "ticket": StructuredExtractionPreset(
        format_file="ai/scripts/fixtures/ticket_json_format.json",
        system=TICKET_EXTRACTION_SYSTEM,
        prompt="Cannot log in after password reset. Tried twice. Urgent — authentication.",
    ),
    "classification": StructuredExtractionPreset(
        format_file="ai/scripts/fixtures/classification_json_format.json",
        system=CLASSIFICATION_EXTRACTION_SYSTEM,
        prompt="Charged twice for order ORD-4421. Want refund of $49.99.",
    ),
}
