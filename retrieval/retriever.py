import re

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from config import TOP_K


def tokenize(text):
    if not text:
        return set()

    return set(
        re.findall(
            r"[a-zA-Z_][a-zA-Z0-9_]*",
            text.lower()
        )
    )


def lexical_score(query, text):
    query_tokens = tokenize(query)
    text_tokens = tokenize(text)

    if not query_tokens:
        return 0.0

    overlap = (
        query_tokens
        & text_tokens
    )

    return (
        len(overlap)
        / len(query_tokens)
    )


def filename_score(query, path):
    query_tokens = tokenize(query)

    filename_tokens = tokenize(
        path
    )

    if not query_tokens:
        return 0.0

    overlap = (
        query_tokens
        & filename_tokens
    )

    return (
        len(overlap)
        / len(query_tokens)
    )


def symbol_score(query, symbol):
    query_tokens = tokenize(query)

    symbol_tokens = tokenize(
        symbol
    )

    if not query_tokens:
        return 0.0

    overlap = (
        query_tokens
        & symbol_tokens
    )

    return (
        len(overlap)
        / len(query_tokens)
    )


def task_specific_bonus(
    query,
    chunk
):
    query_lower = query.lower()

    path = chunk.get(
        "path",
        ""
    ).lower()

    content = chunk.get(
        "content",
        ""
    ).lower()

    bonus = 0.0

    # Authentication-related tasks
    auth_words = (
        "login",
        "logout",
        "auth",
        "authentication",
        "password",
        "username"
    )

    if any(
        word in query_lower
        for word in auth_words
    ):
        if "auth" in path:
            bonus += 0.30

        if "login" in content:
            bonus += 0.15

        if "session_state" in content:
            bonus += 0.10

    # UI-related tasks
    ui_words = (
        "ui",
        "page",
        "button",
        "streamlit",
        "interface",
        "sidebar"
    )

    if any(
        word in query_lower
        for word in ui_words
    ):
        if (
            "ui.py" in path
            or "app.py" in path
        ):
            bonus += 0.25

        if "streamlit" in content:
            bonus += 0.10

    # Testing/error tasks
    error_words = (
        "error",
        "fix",
        "bug",
        "crash",
        "test",
        "exception"
    )

    if any(
        word in query_lower
        for word in error_words
    ):
        if "test" in path:
            bonus += 0.20

    return bonus


def retrieve_relevant_chunks(
    query,
    chunks,
    embeddings,
    top_k=TOP_K
):
    if not chunks:
        return []

    from retrieval.embeddings import (
        embed_query
    )

    query_embedding = embed_query(
        query
    )

    similarities = cosine_similarity(
        [query_embedding],
        embeddings
    )[0]

    results = []

    for index, chunk in enumerate(
        chunks
    ):
        semantic = float(
            similarities[index]
        )

        lexical = lexical_score(
            query,
            chunk.get(
                "content",
                ""
            )
        )

        filename = filename_score(
            query,
            chunk.get(
                "path",
                ""
            )
        )

        symbol = symbol_score(
            query,
            chunk.get(
                "symbol",
                ""
            )
        )

        bonus = task_specific_bonus(
            query,
            chunk
        )

        final_score = (
            semantic * 0.55
            + lexical * 0.20
            + filename * 0.10
            + symbol * 0.10
            + bonus
        )

        result = dict(
            chunk
        )

        result[
            "similarity"
        ] = semantic

        result[
            "retrieval_score"
        ] = final_score

        result[
            "semantic_score"
        ] = semantic

        result[
            "lexical_score"
        ] = lexical

        results.append(
            result
        )

    results.sort(
        key=lambda item: (
            item[
                "retrieval_score"
            ]
        ),
        reverse=True
    )

    return results[
        :top_k
    ]