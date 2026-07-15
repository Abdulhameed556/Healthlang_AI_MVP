"""Protocols for chat system v1 agents."""
from typing import Protocol, TypeVar

InputT = TypeVar("InputT", contravariant=True)
OutputT = TypeVar("OutputT", covariant=True)


class IChatSystemAgent(Protocol[InputT, OutputT]):
    """One chat-system agent with a typed run contract."""

    @property
    def name(self) -> str: ...

    async def run(self, input: InputT) -> OutputT: ...
