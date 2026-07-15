"""Unit tests: ai/src/infrastructure/llm/registry.py"""
import pytest

from ai.src.domain.llm.types import SingleTaskAgentRequest, SingleTaskAgentResult
from ai.src.infrastructure.llm.providers.base import BaseSingleTaskAgentProvider
from ai.src.infrastructure.llm.registry import (
    clear_providers,
    get_provider,
    list_providers,
    register_provider,
)


class _FakeProvider(BaseSingleTaskAgentProvider):
    @property
    def name(self) -> str:
        return "fake"

    async def run(self, request: SingleTaskAgentRequest) -> SingleTaskAgentResult:
        return SingleTaskAgentResult(
            content="ok",
            provider=self.name,
            model=request.model,
        )

    async def stream(self, request: SingleTaskAgentRequest):
        yield "ok"


@pytest.fixture(autouse=True)
def _clean_registry() -> None:
    clear_providers()
    yield
    clear_providers()


def test_register_and_get_provider() -> None:
    register_provider(_FakeProvider())
    provider = get_provider("fake")
    assert provider.name == "fake"


def test_register_duplicate_raises() -> None:
    register_provider(_FakeProvider())
    with pytest.raises(ValueError, match="already registered"):
        register_provider(_FakeProvider())


def test_get_unknown_provider_raises() -> None:
    with pytest.raises(KeyError, match="Unknown LLM provider"):
        get_provider("missing")


def test_list_providers_sorted() -> None:
    class _B(BaseSingleTaskAgentProvider):
        @property
        def name(self) -> str:
            return "b"

        async def run(self, request): ...

        async def stream(self, request):
            yield ""

    class _A(BaseSingleTaskAgentProvider):
        @property
        def name(self) -> str:
            return "a"

        async def run(self, request): ...

        async def stream(self, request):
            yield ""

    register_provider(_B())
    register_provider(_A())
    assert list_providers() == ["a", "b"]
