import pytest

from src.ctv.scoring import SCORE_EXAMPLES, compute_ctv_score


@pytest.mark.parametrize(
    "harm,comp,tool_rating,expected_score,expected_action",
    [
        (False, False, "safe", 0.0, "allow"),
        (False, False, "unsafe", 0.2, "allow"),
        (False, True, "safe", 0.4, "modify"),
        (True, False, "uncertain", 0.5, "modify"),
        (True, True, "safe", 0.8, "block"),
        (True, True, "unsafe", 1.0, "block"),
    ],
)
def test_ctv_scoring(harm, comp, tool_rating, expected_score, expected_action):
    score, action = compute_ctv_score(harm, comp, tool_rating)
    assert score == expected_score
    assert action == expected_action


def test_score_examples_match_table9():
    for row in SCORE_EXAMPLES:
        score, action = compute_ctv_score(
            row["request_harmful"],
            row["compositional_risk"],
            row["tool_safety"],
        )
        assert score == row["score"]
        assert action == row["action"]


def test_ctv_threshold_changes_block_behavior():
    score, action = compute_ctv_score(
        True,
        False,
        "uncertain",
        threshold=0.6,
    )
    assert score == 0.5
    assert action == "modify"


def test_ctv_weight_override_is_applied():
    score, action = compute_ctv_score(
        True,
        True,
        "safe",
        weights={"w1": 0.3, "w2": 0.6, "w3": 0.1},
    )
    assert score == 1.0
    assert action == "block"
