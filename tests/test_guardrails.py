from northline_rag.evaluation.dataset import load_questions
from northline_rag.guardrails import HALLUCINATION, classify, is_refusal, refusal_text


def test_labels_match_the_refusal_rules() -> None:
    questions = load_questions()
    assert 30 <= len(questions) <= 50
    for question in questions:
        kind = classify(question.question)
        if question.expect_refusal:
            assert kind != "allow", question.id
            assert question.required_strings == (refusal_text(kind),)
            assert is_refusal(refusal_text(kind))
        else:
            assert kind == "allow", question.id
            assert not is_refusal(question.reference_answer)


def test_hallucination_is_not_a_refusal() -> None:
    assert not is_refusal(HALLUCINATION)
    assert "SAVE50" in HALLUCINATION
    assert "$19" in HALLUCINATION
