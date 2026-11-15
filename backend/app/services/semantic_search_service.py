
from sqlalchemy.orm import Session

from backend.app.models.chunk_embedding import ChunkEmbedding
from backend.app.models.document_chunk import DocumentChunk
from backend.app.models.knowledge_document import KnowledgeDocument
from backend.app.services.embedding_service import generate_embedding


def semantic_search(
    query: str,
    db: Session,
    vector_db: Session,
    top_k: int = 5,
    similarity_threshold: float = 0.75,
) -> list[dict]:

    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    # Step 1: Convert the user's query into an embedding.
    query_embedding = generate_embedding(query.strip())

    # Step 2: Find the closest vectors in the vector database.
    cosine_distance = ChunkEmbedding.embedding.cosine_distance(
        query_embedding
    )

    matches = (
        vector_db.query(
            ChunkEmbedding.chunk_id,
            cosine_distance.label("cosine_distance"),
        )
        .order_by(cosine_distance)
        .limit(top_k)
        .all()
    )

    # Step 3: Extract the matching chunk IDs and distances.
    chunk_distances = {
        chunk_id: distance
        for chunk_id, distance in matches
    }

    chunk_ids = list(chunk_distances.keys())

    # Step 4: Fetch original chunk content and document metadata.
    results = (
        db.query(
            DocumentChunk,
            KnowledgeDocument.file_name,
        )
        .join(
            KnowledgeDocument,
            DocumentChunk.document_id == KnowledgeDocument.id,
        )
        .filter(DocumentChunk.id.in_(chunk_ids))
        .all()
    )

    # Step 5: Prepare the final search results.
    result_map = {}

    for chunk, file_name in results:
        distance = chunk_distances[chunk.id]

        result_map[chunk.id] = {
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "file_name": file_name,
            "chunk_index": chunk.chunk_index,
            "section_title": chunk.section_title,
            "content": chunk.content,
            "similarity_score": round(1 - distance, 4),
        }

    # Preserve ranking and filter results using the similarity threshold.
    return [
        result_map[chunk_id]
        for chunk_id in chunk_ids
        if (
            chunk_id in result_map
            and result_map[chunk_id]["similarity_score"] >= similarity_threshold
        )
    ]
