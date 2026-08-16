"""
Retrieval step of the RAG pipeline: turns a natural-language question
into an embedding and fetches the most relevant indexed code chunks
for a given repository.
"""
from dataclasses import dataclass

from rag.embeddings import embed_query
from rag.vector_store import RetrievedChunk, collection_name_for_repo, get_vector_store

# A distance above this is treated as "not relevant enough" (Chroma's
# default distance metric is L2 on normalized embeddings; tune per
# embedding model if you swap providers).
_MAX_RELEVANT_DISTANCE = 1.35


@dataclass
class RetrievalResult:
    chunks: list[RetrievedChunk]
    sufficient: bool


def retrieve_relevant_chunks(repository_id: str, question: str, top_k: int = 8) -> RetrievalResult:
    store = get_vector_store()
    collection = collection_name_for_repo(repository_id)
    query_embedding = embed_query(question)
    results = store.query(collection, query_embedding, top_k=top_k)

    relevant = [r for r in results if r.distance <= _MAX_RELEVANT_DISTANCE]
    sufficient = len(relevant) > 0

    return RetrievalResult(chunks=relevant or results, sufficient=sufficient)
