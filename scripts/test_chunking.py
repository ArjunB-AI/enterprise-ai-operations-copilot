
from backend.app.db.session import SessionLocal
from backend.app.models.knowledge_document import KnowledgeDocument
from backend.app.services.chunking_service import create_document_chunks
from backend.app.services.embedding_service import get_embedding_model


def test_chunking():
    db = SessionLocal()

    try:
        documents = (
            db.query(KnowledgeDocument)
            .order_by(KnowledgeDocument.id.asc())
            .all()
        )

        model = get_embedding_model()
        tokenizer = model.tokenizer

        total_chunks = 0
        total_oversized = 0

        for document in documents:
            if not document.extracted_text:
                print(f"Skipping document {document.id}: No text.")
                continue

            chunks = create_document_chunks(document.extracted_text)

            oversized = 0
            maximum_tokens = 0

            for chunk in chunks:
                tokens = tokenizer.encode(
                    chunk["content"],
                    add_special_tokens=True,
                    truncation=False,
                )

                token_count = len(tokens)
                maximum_tokens = max(maximum_tokens, token_count)

                if token_count > model.max_seq_length:
                    oversized += 1

            total_chunks += len(chunks)
            total_oversized += oversized

            print(
                f"\nDocument ID: {document.id} | "
                f"File: {document.file_name}"
            )
            print(f"Generated chunks: {len(chunks)}")
            print(f"Maximum token count: {maximum_tokens}")
            print(f"Chunks exceeding limit: {oversized}")

        print("\nOverall validation")
        print("------------------")
        print(f"Total generated chunks: {total_chunks}")
        print(f"Total oversized chunks: {total_oversized}")

        if total_oversized == 0:
            print("All documents passed validation.")
        else:
            print("Some chunks exceed the model limit.")

    finally:
        db.close()


if __name__ == "__main__":
    test_chunking()
