
from backend.app.db.session import SessionLocal
from backend.app.models.knowledge_document import KnowledgeDocument
from backend.app.services.chunking_service import store_document_chunks


def process_existing_documents():
    db = SessionLocal()

    try:
        documents = (
            db.query(KnowledgeDocument)
            .order_by(KnowledgeDocument.id.asc())
            .all()
        )

        total_chunks = 0

        for document in documents:
            if not document.extracted_text:
                print(
                    f"Skipping document {document.id}: "
                    "No extracted text available."
                )
                continue

            chunk_count = store_document_chunks(
                db=db,
                document_id=document.id,
                text=document.extracted_text,
            )

            db.commit()

            total_chunks += chunk_count

            print(
                f"Document ID: {document.id} | "
                f"File: {document.file_name} | "
                f"Chunks saved: {chunk_count}"
            )

        print(f"\nTotal chunks saved: {total_chunks}")
        print("Document chunk storage completed.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    process_existing_documents()


# from backend.app.db.session import SessionLocal
# from backend.app.models.knowledge_document import KnowledgeDocument
# from backend.app.services.chunking_service import create_document_chunks


# def process_existing_documents():
#     db = SessionLocal()

#     try:
#         documents = (
#             db.query(KnowledgeDocument)
#             .order_by(KnowledgeDocument.id.asc())
#             .all()
#         )

#         for document in documents:
#             if not document.extracted_text:
#                 print(
#                     f"Skipping document {document.id}: "
#                     "No extracted text available."
#                 )
#                 continue

#             chunks = create_document_chunks(document.extracted_text)

#             print(f"\nDocument ID: {document.id}")
#             print(f"File: {document.file_name}")
#             print(f"Total chunks: {len(chunks)}")

#             print("\nFirst 5 chunks:")

#             for chunk in chunks[:5]:
#                 print(
#                     f"Index: {chunk['chunk_index']} | "
#                     f"Tokens: {chunk['token_count']} | "
#                     f"Section: {chunk['section_title']}"
#                 )

#             long_titles = [
#                 chunk for chunk in chunks
#                 if chunk["section_title"]
#                 and len(chunk["section_title"]) > 255
#             ]

#             print(
#                 "Section titles exceeding 255 characters: "
#                 f"{len(long_titles)}"
#             )

#         print("\nChunking verification completed.")

#     except Exception:
#         raise

#     finally:
#         db.close()


# if __name__ == "__main__":
#     process_existing_documents()
