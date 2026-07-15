"""In-memory dataset store for uploaded chat evaluation test cases."""
from ai.src.domain.chat_evaluation.entities import ChatEvalDataset
from ai.src.domain.chat_evaluation.interfaces import IDatasetStore

_store: dict[str, ChatEvalDataset] = {}


class InMemoryDatasetStore(IDatasetStore):
    async def save(self, dataset: ChatEvalDataset) -> None:
        _store[dataset.dataset_id] = dataset

    async def get(self, dataset_id: str) -> ChatEvalDataset | None:
        return _store.get(dataset_id)


_instance: InMemoryDatasetStore | None = None


def get_dataset_store() -> InMemoryDatasetStore:
    global _instance
    if _instance is None:
        _instance = InMemoryDatasetStore()
    return _instance
