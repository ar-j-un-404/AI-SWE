from sentence_transformers import (
    SentenceTransformer
)

from config import EMBEDDING_MODEL


_model = None


def get_embedding_model():
    global _model

    if _model is None:

        _model = SentenceTransformer(
            EMBEDDING_MODEL
        )

    return _model


def embed_chunks(chunks):
    model = get_embedding_model()

    texts = []

    for chunk in chunks:

        text = (
            f"File: {chunk['path']}\n"
            f"Type: {chunk['type']}\n"
            f"Symbol: {chunk['symbol']}\n"
            f"{chunk['content']}"
        )

        texts.append(text)

    return model.encode(
        texts,
        normalize_embeddings=True
    )


def embed_query(query):
    model = get_embedding_model()

    return model.encode(
        [query],
        normalize_embeddings=True
    )[0]