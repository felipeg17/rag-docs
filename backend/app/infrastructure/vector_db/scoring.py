"""Score conversion shared by both vector backends."""

COSINE_SPACE = "cosine"


def cosine_distance_to_similarity(distance: float) -> float:
    """Map a cosine distance in [0, 2] to a similarity in [0, 1].

    Distances >= 1 (orthogonal or opposite vectors) map to 0, and float noise just below 0
    maps to 1. The function is monotone non-increasing, so result order is preserved.
    """
    return min(1.0, max(0.0, 1.0 - distance))
