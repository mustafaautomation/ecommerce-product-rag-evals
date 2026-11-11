from northline_rag.chunking import chunk_document, load_chunks
from northline_rag.corpus import load_corpus
from northline_rag.types import Document


def test_short_document_is_one_chunk() -> None:
    document = Document(doc_id="note", title="Note", body="One fact.\n\nAnother fact.")
    chunks = chunk_document(document, max_chars=500)
    assert len(chunks) == 1
    assert chunks[0].chunk_id == "note-0"
    assert "One fact." in chunks[0].body
    assert chunks[0].text.startswith("Note\n")


def test_chunker_overlaps_paragraphs() -> None:
    paragraphs = [f"Paragraph {index} has thirty characters." for index in range(4)]
    document = Document(doc_id="long", title="Long", body="\n\n".join(paragraphs))
    chunks = chunk_document(document, max_chars=80)
    assert len(chunks) >= 2
    bodies = [chunk.body for chunk in chunks]
    assert any(paragraphs[1] in body for body in bodies)
    assert sum(paragraphs[1] in body for body in bodies) >= 2


def test_catalog_documents_stay_single_chunks() -> None:
    documents = load_corpus()
    chunks = load_chunks()
    assert 15 <= len(documents) <= 30
    assert len(chunks) == len(documents)
    about = next(doc for doc in documents if doc.doc_id == "about")
    assert "made-up" in about.body
    assert "synthetic" in about.body
