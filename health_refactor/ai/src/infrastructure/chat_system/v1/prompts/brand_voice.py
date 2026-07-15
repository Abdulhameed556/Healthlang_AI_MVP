"""Shared brand and personalization text for chat-system prompts."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from backend.src.domain.agents.brand_personalization import (
    DEFAULT_AGENT_TIMEZONE,
    BrandConfig,
    PersonalizationConfig,
    brand_config_from_dict,
    personalization_config_from_dict,
)
from backend.src.domain.agents.timezones import normalize_agent_timezone

DEFAULT_BRAND = brand_config_from_dict(None)
DEFAULT_PERSONALIZATION = personalization_config_from_dict(None)


def resolve_agent_identity_name(brand: BrandConfig, agent_name: str) -> str:
    """Customer-facing name the agent should use for itself."""
    if brand.identity_name.strip():
        return brand.identity_name.strip()
    return agent_name.strip() or "Support Agent"


def format_current_datetime_context(timezone: str) -> str:
    """Current date/time line for system prompts, using the configured IANA timezone."""
    tz_name = normalize_agent_timezone(timezone)
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        tz = ZoneInfo(DEFAULT_AGENT_TIMEZONE)
        tz_name = DEFAULT_AGENT_TIMEZONE
    now = datetime.now(tz)
    formatted = now.strftime("%A, %B %d, %Y %H:%M %Z")
    return f"- Current date and time ({tz_name}): {formatted}"


def format_brand_identity(brand: BrandConfig, agent_name: str) -> str:
    identity_name = resolve_agent_identity_name(brand, agent_name)
    company_name = brand.company_name.strip() or agent_name
    languages = ", ".join(brand.languages) if brand.languages else "english"
    lines = [
        "Brand identity:",
        f"- Your name: {identity_name}",
        f"- Company: {company_name}",
        f"- Supported languages: {languages}",
        format_current_datetime_context(brand.timezone),
        "- Stay on-brand for this company in every reply.",
    ]
    if brand.prompt.strip():
        lines.append(f"- Brand voice instructions: {brand.prompt.strip()}")
    return "\n".join(lines)


def format_personalization(personalization: PersonalizationConfig) -> str:
    tone = personalization.tone_profile.replace("_", " ")
    lines = [
        "Communication style:",
        f"- Tone profile: {tone}",
        f"- Formality: {personalization.formality}",
        (
            "- Pacing: "
            f"{personalization.pacing} on a 0.5–2.0 scale "
            "(lower = slower and more detailed, higher = faster and more concise)"
        ),
    ]
    if personalization.enable_sentiment_analysis:
        lines.append("- Adapt empathy and reassurance to the customer's sentiment.")
    if personalization.custom_greeting.strip():
        lines.append(
            "- Greeting style reference (use this ONLY on your first reply of a new session; "
            "never repeat or reintroduce this greeting on later turns): "
            f"{personalization.custom_greeting.strip()}"
        )
    if personalization.custom_sign_off.strip():
        lines.append(
            f"- Sign-off style reference: {personalization.custom_sign_off.strip()} "
            "(use in message when appropriate; do not treat this alone as grounds for "
            "end_conversation)"
        )
    if personalization.voice_identity:
        lines.append(
            f"- Voice identity (voice channel only): {personalization.voice_identity}"
        )
    return "\n".join(lines)


def format_brand_voice_section(
    *,
    agent_name: str,
    brand_config: BrandConfig | None = None,
    personalization_config: PersonalizationConfig | None = None,
) -> str:
    brand = brand_config or DEFAULT_BRAND
    personalization = personalization_config or DEFAULT_PERSONALIZATION
    name = agent_name.strip() or "Support Agent"
    return "\n\n".join(
        [
            format_brand_identity(brand, name),
            format_personalization(personalization),
        ]
    )
