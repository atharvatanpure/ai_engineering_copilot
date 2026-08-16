"""
Ties the RAG pipeline together for a full (re-)index of a repository:

File Scanner -> Code Parser/Chunker -> Embeddings -> Vector DB

Also mirrors indexing outcomes (per-file chunk counts, indexed flags)
back into PostgreSQL via SQLAlchemy models.
"""
from sqlalchemy.orm import Session

from database import models
from rag.chunker import chunk_file
from rag.embeddings import embed_texts
from rag.vector_store import collection_name_for_repo, get_vector_store
from services.repository import ScanResult


def index_repository(db: Session, repository: models.Repository, scan: ScanResult) -> int:
    """
    Chunks and embeds every scanned file, upserts into the vector store,
    and updates RepositoryFile rows. Returns the total number of chunks indexed.
    """
    store = get_vector_store()
    collection = collection_name_for_repo(repository.id)
    store.delete_collection(collection)  # clean slate on re-index

    total_chunks = 0
    db.query(models.RepositoryFile).filter(
        models.RepositoryFile.repository_id == repository.id
    ).delete()

    all_ids: list[str] = []
    all_texts: list[str] = []
    all_metadatas: list[dict] = []

    for scanned_file in scan.files:
        chunks = chunk_file(scanned_file.relative_path, scanned_file.language, scanned_file.text)

        for i, chunk in enumerate(chunks):
            chunk_id = f"{repository.id}:{scanned_file.relative_path}:{chunk.start_line}-{chunk.end_line}:{i}"
            all_ids.append(chunk_id)
            all_texts.append(_build_embedding_text(repository, chunk))
            all_metadatas.append(
                {
                    "repository": repository.name,
                    "file_path": chunk.file_path,
                    "language": chunk.language,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "symbol": chunk.symbol,
                    "snippet": chunk.text[:1200],
                }
            )

        db.add(
            models.RepositoryFile(
                repository_id=repository.id,
                file_path=scanned_file.relative_path,
                language=scanned_file.language,
                line_count=scanned_file.line_count,
                size_bytes=scanned_file.size_bytes,
                chunk_count=len(chunks),
                indexed=len(chunks) > 0,
            )
        )
        total_chunks += len(chunks)

    # Embed and upsert in manageable batches so a single huge repo
    # doesn't build one giant in-memory request.
    batch_size = 200
    embeddings = embed_texts(all_texts) if all_texts else []
    for i in range(0, len(all_ids), batch_size):
        store.upsert(
            collection,
            ids=all_ids[i:i + batch_size],
            embeddings=embeddings[i:i + batch_size],
            documents=all_texts[i:i + batch_size],
            metadatas=all_metadatas[i:i + batch_size],
        )

    db.flush()
    return total_chunks


def _build_embedding_text(repository: models.Repository, chunk) -> str:
    """Prefix each chunk with lightweight metadata so the embedding
    captures file/symbol context, not just raw code tokens."""
    header = f"# {chunk.file_path}"
    if chunk.symbol:
        header += f" :: {chunk.symbol}"
    header += f" (lines {chunk.start_line}-{chunk.end_line})"
    return f"{header}\n{chunk.text}"
