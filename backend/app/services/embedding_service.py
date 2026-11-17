
import logging

from sentence_transformers import SentenceTransformer


logger = logging.getLogger(__name__)

MODEL_NAME = "BAAI/bge-small-en-v1.5"

embedding_model = None


def get_embedding_model():
    global embedding_model

    if embedding_model is None:
        logger.info(
            "Loading embedding model | model=%s",
            MODEL_NAME,
        )

        try:
            embedding_model = SentenceTransformer(MODEL_NAME)

            logger.info(
                "Embedding model loaded successfully | model=%s | dimensions=%s",
                MODEL_NAME,
                embedding_model.get_embedding_dimension(),
            )

        except Exception:
            logger.exception(
                "Failed to load embedding model | model=%s",
                MODEL_NAME,
            )
            raise

    else:
        logger.debug("Reusing already loaded embedding model.")

    return embedding_model


def generate_embedding(text: str) -> list[float]:
    if not text or not text.strip():
        logger.warning("Embedding generation rejected: empty input.")
        raise ValueError("Cannot generate embedding for empty text.")

    logger.debug("Single embedding generation started.")

    try:
        model = get_embedding_model()

        embedding = model.encode(
            text,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        logger.info(
            "Single embedding generated successfully | dimensions=%s",
            len(embedding),
        )

        return embedding.tolist()

    except Exception:
        logger.exception("Single embedding generation failed.")
        raise


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    if not texts:
        logger.warning("Batch embedding generation skipped: empty input.")
        return []

    for index, text in enumerate(texts):
        if not text or not text.strip():
            logger.warning(
                "Batch embedding generation rejected | empty_text_index=%s",
                index,
            )
            raise ValueError(
                f"Cannot generate embedding: text at index {index} is empty."
            )

    logger.info(
        "Batch embedding generation started | text_count=%s",
        len(texts),
    )

    try:
        model = get_embedding_model()

        embeddings = model.encode(
            texts,
            batch_size=32,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=True,
        )

        logger.info(
            "Batch embedding generation completed | count=%s | dimensions=%s",
            len(embeddings),
            embeddings.shape[1],
        )

        return embeddings.tolist()

    except Exception:
        logger.exception("Batch embedding generation failed.")
        raise RuntimeError(
            "Failed to generate embeddings for the provided texts."
        ) from None
