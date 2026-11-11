
from sentence_transformers import SentenceTransformer


MODEL_NAME = "BAAI/bge-small-en-v1.5"

embedding_model = None


def get_embedding_model():
    global embedding_model

    if embedding_model is None:
        print(f"Loading embedding model: {MODEL_NAME}")

        embedding_model = SentenceTransformer(MODEL_NAME)

        print("Embedding model loaded successfully.")

    return embedding_model



def generate_embedding(text: str) -> list[float]:
    if not text or not text.strip():
        raise ValueError("Cannot generate embedding for empty text.")

    model = get_embedding_model()

    embedding = model.encode(
        text,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    return embedding.tolist()


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    for index, text in enumerate(texts):
        if not text or not text.strip():
            raise ValueError(
                f"Cannot generate embedding: text at index {index} is empty."
            )

    model = get_embedding_model()

    try:
        embeddings = model.encode(
            texts,
            batch_size=32,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=True,
        )

        return embeddings.tolist()

    except Exception as exc:
        raise RuntimeError(
            "Failed to generate embeddings for the provided texts."
        ) from exc

