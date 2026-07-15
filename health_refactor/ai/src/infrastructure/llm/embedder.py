"""OpenAI embeddings implementation of IEmbedder."""
import asyncio

from openai import OpenAI

from ai.src.core.config import settings


def _embed_sync(client: OpenAI, model: str, texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(model=model, input=texts)
    return [item.embedding for item in response.data]


class OpenAIEmbedder:
    def __init__(self) -> None:
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.default_embedding_model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return await asyncio.to_thread(_embed_sync, self._client, self._model, texts)
