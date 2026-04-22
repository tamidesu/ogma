"""Unit tests for MetricsCalculator."""
import pytest

from app.simulation.metrics import MetricsCalculator


@pytest.fixture
def calc():
    return MetricsCalculator()


class TestMetricsCalculator:
    def test_level_1_at_zero_xp(self, calc):
        assert calc.level_for_xp(0) == 1

    def test_level_2_at_100_xp(self, calc):
        assert calc.level_for_xp(100) == 2

    def test_level_increases_correctly(self, calc):
        assert calc.level_for_xp(250) == 3
        assert calc.level_for_xp(499) == 2
        assert calc.level_for_xp(500) == 4

    def test_xp_to_next_level(self, calc):
        assert calc.xp_to_next_level(0, 1) == 100
        assert calc.xp_to_next_level(50, 1) == 50
        assert calc.xp_to_next_level(100, 2) == 150

    def test_final_score_clamped_at_100(self, calc):
        score = calc.compute_final_score(
            {"reputation": 100, "risk": 0, "team_morale": 100, "score": 0},
            "software_engineer",
        )
        assert score <= 100.0

    def test_final_score_not_negative(self, calc):
        score = calc.compute_final_score(
            {"reputation": 0, "risk": 100, "team_morale": 0, "score": 0},
            "software_engineer",
        )
        assert score >= 0.0

    def test_step_score_positive_for_improvements(self, calc):
        before = {"reputation": 50, "risk": 50, "score": 0}
        after  = {"reputation": 65, "risk": 40, "score": 0}
        score = calc.compute_step_score(before, after, "software_engineer")
        assert score > 0

    def test_unknown_profession_uses_default_weights(self, calc):
        score = calc.compute_final_score({"reputation": 60}, "unknown_job")
        assert isinstance(score, float)
