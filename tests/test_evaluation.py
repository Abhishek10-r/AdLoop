import pytest

from src.evaluation import cohen_kappa, confusion, evaluate, normalise


def test_normalise_accepts_common_spellings():
    assert normalise(" Pass ") == "pass"
    assert normalise("rejected") == "fail"
    with pytest.raises(ValueError):
        normalise("maybe")


def test_confusion_treats_fail_as_positive():
    human = ["fail", "fail", "pass", "pass"]
    judge = ["fail", "pass", "fail", "pass"]
    assert confusion(human, judge) == {"tp": 1, "fn": 1, "fp": 1, "tn": 1}


def test_perfect_agreement():
    labels = ["pass", "fail", "pass", "fail"]
    m = evaluate(labels, labels)
    assert m["agreement"] == 1.0
    assert m["precision_fail"] == m["recall_fail"] == m["f1_fail"] == 1.0
    assert m["cohen_kappa"] == 1.0


def test_kappa_is_zero_when_judge_ignores_the_input():
    # A judge that always says "pass" agrees 75% of the time here, but adds nothing.
    human = ["pass", "pass", "pass", "fail"]
    judge = ["pass", "pass", "pass", "pass"]
    assert evaluate(human, judge)["agreement"] == 0.75
    assert cohen_kappa(human, judge) == 0.0


def test_known_kappa_value():
    # Textbook case: observed 0.70, expected 0.50 -> kappa 0.40.
    human = ["fail"] * 5 + ["pass"] * 5
    judge = ["fail"] * 4 + ["pass"] + ["fail"] * 2 + ["pass"] * 3
    assert cohen_kappa(human, judge) == pytest.approx(0.4)
