
from backend.app.db.session import SessionLocal
from backend.app.db.vector_session import VectorSessionLocal
from backend.app.services.rag_service import generate_rag_response


def main():
    db = SessionLocal()
    vector_db = VectorSessionLocal()

    try:
        #query = "How can an employee get a laptop replaced?"
        query = "What food is available in the company cafeteria?"

        print(f"\nQuestion: {query}\n")

        result = generate_rag_response(
            query=query,
            db=db,
            vector_db=vector_db,
        )

        print("\nAI Answer:\n")
        print(result["answer"])

        print("\nSources:\n")

        for source in result["sources"]:
            print(
                f"{source['source']}: {source['file_name']} "
                f"(chunk {source['chunk_index']}, "
                f"similarity {source['similarity_score']})"
            )

    finally:
        db.close()
        vector_db.close()


if __name__ == "__main__":
    main()
