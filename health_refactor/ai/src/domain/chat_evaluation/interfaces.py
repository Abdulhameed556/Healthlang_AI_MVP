"""Interfaces (abstract contracts) for the chat evaluation system."""
from abc import ABC, abstractmethod

from ai.src.domain.chat_evaluation.entities import (
    ChatEvalDataset,
    ChatEvalReport,
)


class IRunStore(ABC):
    @abstractmethod
    async def save(self, report: ChatEvalReport) -> None: ...

    @abstractmethod
    async def get(self, run_id: str) -> ChatEvalReport | None: ...

    @abstractmethod
    async def list(
        self,
        agent_id: str | None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ChatEvalReport], int]: ...


class IDatasetStore(ABC):
    @abstractmethod
    async def save(self, dataset: ChatEvalDataset) -> None: ...

    @abstractmethod
    async def get(self, dataset_id: str) -> ChatEvalDataset | None: ...
