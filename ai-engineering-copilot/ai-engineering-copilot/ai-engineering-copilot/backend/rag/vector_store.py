"""
Vector database abstraction.

`VectorStore` is the interface the rest of the app depends on.
`ChromaVectorStore` is the MVP implementation. To swap in Qdrant (or
another backend) later, implement `VectorStore` and change
`get_vector_store()` — no other module needs to change.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from config import get_settings

settings = get_settings()


@dataclass
class RetrievedChunk:
    id: str
    text: str
    metadata: dict[str, Any]
    distance: float


class VectorStore(ABC):
    @abstractmethod
    def upsert(
        self,
        collection: str,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        ...

    @abstractmethod
    def query(
        self, collection: str, embedding: list[float], top_k: int = 8
    ) -> list[RetrievedChunk]:
        ...

    @abstractmethod
    def delete_collection(self, collection: str) -> None:
        ...

    @abstractmethod
    def count(self, collection: str) -> int:
        ...


class ChromaVectorStore(VectorStore):
    def __init__(self):
        import chromadb

        self.client = chromadb.PersistentClient(path=settings.chroma_persist_dir)

    def _get_or_create(self, collection: str):
        return self.client.get_or_create_collection(name=collection)

    def upsert(
        self,
        collection: str,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        if not ids:
            return
        coll = self._get_or_create(collection)
        # Chroma requires JSON-primitive metadata values only.
        clean_meta = [
            {k: v for k, v in m.items() if isinstance(v, (str, int, float, bool)) or v is None}
            for m in metadatas
        ]
        coll.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=clean_meta)

    def query(
        self, collection: str, embedding: list[float], top_k: int = 8
    ) -> list[RetrievedChunk]:
        try:
            coll = self.client.get_collection(name=collection)
        except Exception:
            return []
        result = coll.query(query_embeddings=[embedding], n_results=top_k)
        out: list[RetrievedChunk] = []
        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        dists = result.get("distances", [[]])[0]
        for i in range(len(ids)):
            out.append(
                RetrievedChunk(id=ids[i], text=docs[i], metadata=metas[i] or {}, distance=dists[i])
            )
        return out

    def delete_collection(self, collection: str) -> None:
        try:
            self.client.delete_collection(name=collection)
        except Exception:
            pass

    def count(self, collection: str) -> int:
        try:
            return self.client.get_collection(name=collection).count()
        except Exception:
            return 0


def collection_name_for_repo(repository_id: str) -> str:
    return f"repo_{repository_id.replace('-', '')}"


@lru_cache
def get_vector_store() -> VectorStore:
    return ChromaVectorStore()
