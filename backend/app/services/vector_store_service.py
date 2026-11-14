
from sqlalchemy.orm import Session

from backend.app.models.document_chunk import DocumentChunk
from backend.app.models.chunk_embedding import ChunkEmbedding
from backend.app.services.embedding_service import generate_embeddings


def store_chunk_embeddings(
    db: Session,
    vector_db: Session,
) -> int:
    # 1. Retrieve all document chunks from the main database.
    chunks = (
        db.query(DocumentChunk)
        .order_by(
            DocumentChunk.document_id,
            DocumentChunk.chunk_index,
        )
        .all()
    )

    if not chunks:
        return 0

    # 2. Generate embeddings for all chunk contents.
    texts = [chunk.content for chunk in chunks]
    embeddings = generate_embeddings(texts)

    # 3. Find embeddings that already exist in the vector database.
    chunk_ids = [chunk.id for chunk in chunks]

    existing_records = (
        vector_db.query(ChunkEmbedding)
        .filter(ChunkEmbedding.chunk_id.in_(chunk_ids))
        .all()
    )

    existing_map = {
        record.chunk_id: record
        for record in existing_records
    }

    # 4. Insert new embeddings or update existing ones.
    for chunk, embedding in zip(chunks, embeddings):
        existing_record = existing_map.get(chunk.id)

        if existing_record:
            existing_record.embedding = embedding
        else:
            vector_db.add(
                ChunkEmbedding(
                    chunk_id=chunk.id,
                    embedding=embedding,
                )
            )

    # 5. Save everything permanently.
    try:
        vector_db.commit()
    except Exception:
        vector_db.rollback()
        raise

    return len(chunks)
