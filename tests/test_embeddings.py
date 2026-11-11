import numpy as np

from northline_rag.embeddings import HashingEmbedder


def _cosine(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.dot(left, right))


def test_hashing_embedder_is_deterministic_and_normalized() -> None:
    embedder = HashingEmbedder()
    first = embedder.embed_query("Trailwool Crewneck merino wool")
    second = embedder.embed_query("Trailwool Crewneck merino wool")
    assert first.shape == (embedder.dim,)
    assert np.array_equal(first, second)
    assert abs(float(np.linalg.norm(first)) - 1.0) < 1e-5


def test_empty_query_is_a_zero_vector() -> None:
    embedder = HashingEmbedder()
    vector = embedder.embed_query("the a of")
    assert float(np.linalg.norm(vector)) == 0.0


def test_related_text_is_closer_than_unrelated_text() -> None:
    embedder = HashingEmbedder()
    anchor = embedder.embed_query("Trailwool Crewneck merino wool price")
    related = embedder.embed_query("Trailwool Crewneck merino wool")
    unrelated = embedder.embed_query("cryptocurrency refund schedule")
    assert _cosine(anchor, related) > _cosine(anchor, unrelated)
