
from backend.app.db.session import SessionLocal
from backend.app.db.vector_session import VectorSessionLocal

from backend.app.services.vector_store_service import (
    store_chunk_embeddings,
)


def main():
    db = SessionLocal()
    vector_db = VectorSessionLocal()

    try:
        print("Starting embedding storage...")

        total = store_chunk_embeddings(
            db=db,
            vector_db=vector_db,
        )

        print(f"Successfully stored {total} chunk embeddings.")

    except Exception as exc:
        print(f"Embedding storage failed: {exc}")
        raise

    finally:
        db.close()
        vector_db.close()


if __name__ == "__main__":
    main()
