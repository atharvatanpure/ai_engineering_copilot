from rag import retriever
from rag.vector_store import RetrievedChunk, VectorStore


class FakeVectorStore(VectorStore):
    """In-memory stand-in for ChromaDB used to test retrieval logic in isolation."""

    def __init__(self, canned_results: list[RetrievedChunk]):
        self._canned_results = canned_results

    def upsert(self, collection, ids, embeddings, documents, metadatas):
        pass

    def query(self, collection, embedding, top_k=8):
        return self._canned_results[:top_k]

    def delete_collection(self, collection):
        pass

    def count(self, collection):
        return len(self._canned_results)


def test_retrieve_relevant_chunks_marks_sufficient_when_close_match(monkeypatch):
    close_chunk = RetrievedChunk(
        id="1",
        text="def authenticate_user(): ...",
        metadata={"file_path": "auth.py", "start_line": 1, "end_line": 5},
        distance=0.2,
    )
    fake_store = FakeVectorStore([close_chunk])
    monkeypatch.setattr(retriever, "get_vector_store", lambda: fake_store)
    monkeypatch.setattr(retriever, "embed_query", lambda q: [0.1, 0.2])

    result = retriever.retrieve_relevant_chunks("repo-1", "how does auth work?")

    assert result.sufficient is True
    assert len(result.chunks) == 1


def test_retrieve_relevant_chunks_marks_insufficient_when_no_results(monkeypatch):
    fake_store = FakeVectorStore([])
    monkeypatch.setattr(retriever, "get_vector_store", lambda: fake_store)
    monkeypatch.setattr(retriever, "embed_query", lambda q: [0.1, 0.2])

    result = retriever.retrieve_relevant_chunks("repo-1", "unrelated question")

    assert result.sufficient is False
    assert result.chunks == []
