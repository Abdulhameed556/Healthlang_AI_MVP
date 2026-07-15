"""Unit tests: shared brand voice prompt helpers."""
from unittest.mock import patch

from backend.src.domain.agents.brand_personalization import (
    BrandConfig,
    PersonalizationConfig,
)
from ai.src.infrastructure.chat_system.v1.prompts.brand_voice import (
    format_brand_voice_section,
    resolve_agent_identity_name,
)

_NORMALIZE_TZ_PATH = (
    "ai.src.infrastructure.chat_system.v1.prompts"
    ".brand_voice.normalize_agent_timezone"
)


def test_format_brand_voice_section_includes_tone_and_company() -> None:
    text = format_brand_voice_section(
        agent_name="Support Bot",
        brand_config=BrandConfig(
            company_name="Acme Corp",
            languages=["english"],
            prompt="Always be concise and empathetic.",
            identity_name="Alex",
            timezone="America/New_York",
        ),
        personalization_config=PersonalizationConfig(
            tone_profile="friendly_casual",
            voice_identity=None,
            pacing=1.0,
            formality="balanced",
            custom_greeting="Hey there!",
            custom_sign_off="Cheers,",
            enable_sentiment_analysis=False,
        ),
    )

    assert "Acme Corp" in text
    assert "Your name: Alex" in text
    assert "Current date and time (America/New_York):" in text
    assert "Always be concise and empathetic." in text
    assert "friendly casual" in text
    assert "Hey there!" in text


def test_format_brand_voice_section_omits_empty_prompt() -> None:
    text = format_brand_voice_section(
        agent_name="Support Bot",
        brand_config=BrandConfig(company_name="Acme Corp", languages=["english"]),
    )

    assert "Brand voice instructions:" not in text
    assert "Your name: Support Bot" in text
    assert "Current date and time (UTC):" in text


def test_format_brand_voice_section_normalizes_unsupported_timezone() -> None:
    text = format_brand_voice_section(
        agent_name="Support Bot",
        brand_config=BrandConfig(
            company_name="Acme Corp",
            languages=["english"],
            timezone="America/Detroit",
        ),
    )

    assert "Current date and time (UTC):" in text


def test_resolve_agent_identity_name_prefers_brand_identity() -> None:
    brand = BrandConfig(
        company_name="Acme", languages=["english"], identity_name="Alex"
    )

    assert resolve_agent_identity_name(brand, "Support Bot") == "Alex"


def test_resolve_agent_identity_name_falls_back_to_agent_name() -> None:
    brand = BrandConfig(company_name="Acme", languages=["english"])

    assert resolve_agent_identity_name(brand, "Support Bot") == "Support Bot"


def test_format_current_datetime_context_falls_back_when_tz_invalid() -> None:
    from ai.src.infrastructure.chat_system.v1.prompts.brand_voice import (
        format_current_datetime_context,
    )

    with patch(_NORMALIZE_TZ_PATH, return_value="Not/ARealTimezone"):
        result = format_current_datetime_context("UTC")

    assert "UTC" in result


def test_format_personalization_includes_voice_identity() -> None:
    from ai.src.infrastructure.chat_system.v1.prompts.brand_voice import (
        format_personalization,
    )

    text = format_personalization(
        PersonalizationConfig(
            tone_profile="friendly_casual",
            voice_identity="Echo Alpha",
            pacing=1.0,
            formality="balanced",
            custom_greeting="",
            custom_sign_off="",
            enable_sentiment_analysis=False,
        )
    )

    assert "Voice identity (voice channel only): Echo Alpha" in text
