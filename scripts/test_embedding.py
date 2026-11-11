import math
from backend.app.db.session import SessionLocal
from backend.app.models.document_chunk import DocumentChunk
from backend.app.services.embedding_service import (
    get_embedding_model,
    generate_embedding,
    generate_embeddings,
)


def test_embedding():
    db = SessionLocal()

    try:
        # Load the embedding model
        model = get_embedding_model()

        print("\nModel information")
        print("-----------------")
        print(f"Maximum sequence length: {model.max_seq_length}")
        print(f"Embedding dimensions: {model.get_embedding_dimension()}")

        # Retrieve all stored chunks
        chunks = (
            db.query(DocumentChunk)
            .order_by(
                DocumentChunk.document_id,
                DocumentChunk.chunk_index,
            )
            .all()
        )

        print(f"\nTotal chunks retrieved: {len(chunks)}")

        if not chunks:
            print("No document chunks found.")
            return

        # Generate embedding for the first chunk
        first_chunk = chunks[0]

        embedding = generate_embedding(first_chunk.content)

        # Generate embeddings for all chunks in batches
        chunk_texts = [chunk.content for chunk in chunks]

        embeddings = generate_embeddings(chunk_texts)

        print("\nBatch embedding test")
        print("--------------------")
        print(f"Total chunks: {len(chunk_texts)}")
        print(f"Total embeddings generated: {len(embeddings)}")
        print(f"First embedding dimensions: {len(embeddings[0])}")

        # Validate embedding dimensions
        expected_dimensions = model.get_embedding_dimension()

        invalid_embeddings = [
            index
            for index, embedding in enumerate(embeddings)
            if len(embedding) != expected_dimensions
        ]

        print("\nEmbedding dimension validation")
        print("--------------------------------")
        print(f"Expected dimensions: {expected_dimensions}")
        print(f"Invalid embeddings: {len(invalid_embeddings)}")

        if invalid_embeddings:
            print(f"Invalid embedding indexes: {invalid_embeddings}")
        else:
            print("All embeddings have the correct dimensions.")

        # Validate embedding normalization
        vector_norms = [
            math.sqrt(sum(value * value for value in embedding))
            for embedding in embeddings
        ]

        invalid_norms = [
            index
            for index, norm in enumerate(vector_norms)
            if not math.isclose(norm, 1.0, rel_tol=1e-5, abs_tol=1e-5)
        ]

        print("\nEmbedding normalization validation")
        print("-----------------------------------")
        print(f"First vector norm: {vector_norms[0]:.6f}")
        print(f"Invalid normalized vectors: {len(invalid_norms)}")

        if invalid_norms:
            print(f"Invalid vector indexes: {invalid_norms}")
        else:
            print("All embeddings are normalized.")

        print("\nEmbedding test")
        print("--------------")
        print(f"Document ID: {first_chunk.document_id}")
        print(f"Chunk index: {first_chunk.chunk_index}")
        print(f"Vector dimensions: {len(embedding)}")
        print(f"First 10 values: {embedding[:10]}")

        # Check every chunk using BGE's tokenizer
        tokenizer = model.tokenizer
        max_length = model.max_seq_length

        token_lengths = []

        for chunk in chunks:
            tokens = tokenizer(
                chunk.content,
                add_special_tokens=True,
                truncation=False,
            )["input_ids"]

            token_lengths.append(len(tokens))

        oversized_chunks = [
            length for length in token_lengths
            if length > max_length
        ]

        print("\nToken length verification")
        print("------------------------")
        print(f"Maximum BGE token count: {max(token_lengths)}")
        print(f"Model token limit: {max_length}")
        print(f"Chunks exceeding limit: {len(oversized_chunks)}")

        if oversized_chunks:
            print("Some chunks need adjustment before embedding.")
        else:
            print("All chunks fit within the model token limit.")

    finally:
        db.close()


if __name__ == "__main__":
    test_embedding()
