"""Metadata filter builders shared by both vector DB backends."""


def build_document_filter(
    document_title: str,
    metadata_filter: dict | None = None,
) -> dict:
    """Scope a retrieval to one document, optionally narrowed by a client filter.

    The title clause is always a top-level conjunct, so the client filter can only narrow
    the result. The output is valid for both Chroma (single top-level key, `$and` with 2+
    elements) and PGVector. Client clauses are passed through without validation.

    Args:
        document_title: Value of the `titulo` chunk metadata key.
        metadata_filter: Optional client filter, AND-ed with the document scope.

    Returns:
        `{"titulo": {"$eq": title}}` alone, or `{"$and": [title_clause, *client_clauses]}`.
    """
    clauses: list[dict] = [{"titulo": {"$eq": document_title}}]

    if metadata_filter:
        # Chroma rejects multi-key dicts; PGVector treats them as AND. Split per key.
        clauses.extend({key: value} for key, value in metadata_filter.items())

    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}
