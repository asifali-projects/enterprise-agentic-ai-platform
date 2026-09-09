from app.services.evaluation import score_case


def test_evaluation_exact():
    assert score_case({"answer": "ok"}, {"answer": "ok"}) == 1.0


def test_evaluation_partial():
    assert score_case({"a": 1, "b": 2}, {"a": 1, "b": 3}) == 0.5
