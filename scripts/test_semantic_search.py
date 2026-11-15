
from backend.app.db.session import SessionLocal
from backend.app.db.vector_session import VectorSessionLocal
from backend.app.services.semantic_search_service import semantic_search


def main():
    db = SessionLocal()
    vector_db = VectorSessionLocal()

    try:
        #query = "How can an employee get a laptop replaced?"
        query = "What is the company's cafeteria menu?"

        print(f"\nSearch query: {query}")
        print("\nSearching knowledge base...\n")

        results = semantic_search(
            query=query,
            db=db,
            vector_db=vector_db,
            top_k=5,
        )

        if not results:
            print("No matching documents found.")
            return

        for index, result in enumerate(results, start=1):
            print(f"\n{'=' * 60}")
            print(f"Result {index}")
            print(f"{'=' * 60}")
            print(f"Document: {result['file_name']}")
            print(f"Document ID: {result['document_id']}")
            print(f"Chunk ID: {result['chunk_id']}")
            print(f"Chunk Index: {result['chunk_index']}")
            print(f"Section: {result['section_title']}")
            print(f"Similarity Score: {result['similarity_score']}")
            print(f"\nContent:\n{result['content']}")

    finally:
        db.close()
        vector_db.close()


if __name__ == "__main__":
    main()
