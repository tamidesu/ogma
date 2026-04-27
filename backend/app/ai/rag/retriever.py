"""Abstract RAG retriever interface + shared dataclasses."""
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class RetrievedChunk:
    """A single ranked chunk returned by a tagged retriever.

    Used by the DomainValidator (and any agent that needs source-cited evidence).
    `citation` is the human-readable source string; `tag` is the manifest tag
    so callers can group results by knowledge category.
    """
    text: str
    citation: str
    tag: str
    score: float
    title: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Retriever(ABC):

    @abstractmethod
    def query(self, text: str, filters: dict, top_k: int = 3) -> list[str]:
        """Return top_k relevant document snippets for the given query text."""
        ...

    @abstractmethod
    def is_ready(self) -> bool:
        """Returns True if the retriever has been initialised with documents."""
        ...
