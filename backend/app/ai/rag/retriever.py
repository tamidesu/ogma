"""Abstract RAG retriever interface."""
from abc import ABC, abstractmethod


class Retriever(ABC):

    @abstractmethod
    def query(self, text: str, filters: dict, top_k: int = 3) -> list[str]:
        """Return top_k relevant document snippets for the given query text."""
        ...

    @abstractmethod
    def is_ready(self) -> bool:
        """Returns True if the retriever has been initialised with documents."""
        ...
