
import logging

from sqlalchemy.orm import Session

from backend.app.models.chunk_embedding import ChunkEmbedding
from backend.app.models.document_chunk import DocumentChunk
from backend.app.models.knowledge_document import KnowledgeDocument
from backend.app.services.embedding_service import generate_embedding


logger = logging.getLogger(__name__)


def semantic_search(
    query: str,
    db: Session,
    vector_db: Session,
    top_k: int = 5,
    similarity_threshold: float = 0.75,
) -> list[dict]:

    logger.info(
        "Semantic search started | top_k=%s | threshold=%s",
        top_k,
        similarity_threshold,
    )

    if not query or not query.strip():
        logger.warning("Semantic search rejected: empty query.")
        raise ValueError("Search query cannot be empty.")

    if top_k < 1:
        logger.warning("Semantic search rejected: invalid top_k=%s", top_k)
        raise ValueError("top_k must be at least 1.")

    try:
        # Step 1: Convert the user's query into an embedding.
        logger.info("Generating query embedding.")

        query_embedding = generate_embedding(query.strip())

        logger.info(
            "Query embedding generated | dimensions=%s",
            len(query_embedding),
        )

        # Step 2: Find the closest vectors in the vector database.
        logger.info("Executing vector similarity search.")

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

        logger.info(
            "Vector search completed | match_count=%s",
            len(matches),
        )

        # Step 3: Extract the matching chunk IDs and distances.
        chunk_distances = {
            chunk_id: distance
            for chunk_id, distance in matches
        }

        chunk_ids = list(chunk_distances.keys())

        for chunk_id, distance in chunk_distances.items():
            logger.debug(
                "Vector match | chunk_id=%s | cosine_distance=%.4f | similarity=%.4f",
                chunk_id,
                distance,
                1 - distance,
            )

        if not chunk_ids:
            logger.warning("Vector search returned no matching chunks.")
            return []

        # Step 4: Fetch original chunk content and document metadata.
        logger.info(
            "Fetching original chunks and document metadata | chunk_count=%s",
            len(chunk_ids),
        )

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

        logger.info(
            "Document chunk lookup completed | fetched_count=%s",
            len(results),
        )

        # Step 5: Prepare the final search results.
        result_map = {}

        for chunk, file_name in results:
            distance = chunk_distances[chunk.id]

            similarity_score = round(1 - distance, 4)

            result_map[chunk.id] = {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "file_name": file_name,
                "chunk_index": chunk.chunk_index,
                "section_title": chunk.section_title,
                "content": chunk.content,
                "similarity_score": similarity_score,
            }

            logger.debug(
                "Chunk evaluated | chunk_id=%s | file_name=%s | similarity=%.4f | threshold=%.4f | accepted=%s",
                chunk.id,
                file_name,
                similarity_score,
                similarity_threshold,
                similarity_score >= similarity_threshold,
            )

        # Preserve ranking and filter results using the similarity threshold.
        filtered_results = [
            result_map[chunk_id]
            for chunk_id in chunk_ids
            if (
                chunk_id in result_map
                and result_map[chunk_id]["similarity_score"] >= similarity_threshold
            )
        ]

        logger.info(
            "Semantic search completed | fetched=%s | accepted=%s | rejected=%s",
            len(results),
            len(filtered_results),
            len(results) - len(filtered_results),
        )

        return filtered_results

    except Exception:
        logger.exception("Semantic search failed.")
        raise
