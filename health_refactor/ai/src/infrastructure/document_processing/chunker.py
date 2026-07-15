"""Token-aware text chunker using tiktoken (cl100k_base encoding)."""
import tiktoken


class TiktokenChunker:
    def __init__(self) -> None:
        self._enc = tiktoken.get_encoding("cl100k_base")

    def chunk(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        tokens = self._enc.encode(text)
        if not tokens:
            return []
        chunks: list[str] = []
        start = 0
        while start < len(tokens):
            end = min(start + chunk_size, len(tokens))
            chunks.append(self._enc.decode(tokens[start:end]))
            if end >= len(tokens):
                break
            start = end - overlap
        return chunks
