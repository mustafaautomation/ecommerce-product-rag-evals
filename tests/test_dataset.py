from northline_rag.chunking import load_chunks
from northline_rag.corpus import load_corpus
from northline_rag.evaluation.dataset import load_questions
from northline_rag.generators import select_sentences
from northline_rag.types import Chunk


def test_reference_docs_and_required_strings_exist() -> None:
    documents = {document.doc_id: document for document in load_corpus()}
    chunks = load_chunks()
    by_doc: dict[str, list[Chunk]] = {}
    for chunk in chunks:
        by_doc.setdefault(chunk.doc_id, []).append(chunk)
    for question in load_questions():
        assert question.reference_doc_ids
        for doc_id in question.reference_doc_ids:
            assert doc_id in documents, question.id
        blob = "\n".join(documents[doc_id].body for doc_id in question.reference_doc_ids)
        for required in question.required_strings:
            assert required in blob, question.id
        if not question.expect_refusal:
            sentences = select_sentences(question.question, by_doc[question.reference_doc_ids[0]])
            answer = " ".join(sentences)
            for required in question.required_strings:
                assert required in answer, (question.id, answer)
