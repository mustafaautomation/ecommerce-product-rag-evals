from northline_rag.embeddings import HashingEmbedder
from northline_rag.retrieval import Retriever
from northline_rag.stores.faiss_store import FaissStore
from northline_rag.types import Chunk


def test_inverted_retriever_returns_the_worse_chunk() -> None:
    chunks = (
        Chunk("a-0", "a", "Wool", "Wool\nThe wool sweater is warm.", "The wool sweater is warm."),
        Chunk("b-0", "b", "Tax", "Tax\nSales tax is not quoted.", "Sales tax is not quoted."),
    )
    embedder = HashingEmbedder()
    vectors = embedder.embed_texts([chunk.text for chunk in chunks])
    store = FaissStore(chunks, vectors)
    normal = Retriever(store, embedder, invert=False, k=1)
    flipped = Retriever(store, embedder, invert=True, k=1)
    assert normal.retrieve("wool sweater")[0].doc_id == "a"
    assert flipped.retrieve("wool sweater")[0].doc_id == "b"
