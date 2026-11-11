from northline_rag.evaluation.dataset import load_questions
from northline_rag.guardrails import HALLUCINATION
from northline_rag.pipeline import build_assistant


def test_improved_answers_follow_the_labelled_contract() -> None:
    assistant = build_assistant("improved")
    for question in load_questions():
        result = assistant.answer(question.question)
        retrieved = [chunk.doc_id for chunk in result.chunks]
        assert set(question.reference_doc_ids) & set(retrieved), (question.id, retrieved)
        for required in question.required_strings:
            assert required in result.text, (question.id, result.text)
        assert result.refused is question.expect_refusal
        if question.expect_refusal:
            assert any(result.text in chunk.text for chunk in result.chunks)


def test_baseline_refusal_questions_invent_a_discount() -> None:
    assistant = build_assistant("baseline")
    refusals = [question for question in load_questions() if question.expect_refusal]
    assert refusals
    for question in refusals:
        result = assistant.answer(question.question)
        assert result.text == HALLUCINATION
        assert result.refused is False
