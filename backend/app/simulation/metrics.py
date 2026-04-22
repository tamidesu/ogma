"""
MetricsCalculator — deterministic score computation.
No AI, no DB.
"""


class MetricsCalculator:

    # XP thresholds per level (cumulative)
    XP_THRESHOLDS = [0, 100, 250, 500, 900, 1400, 2000, 2800, 3800, 5000]

    def compute_step_score(
        self,
        metrics_before: dict[str, float],
        metrics_after: dict[str, float],
        profession_slug: str,
    ) -> float:
        """
        Score for a single step = weighted improvement across key metrics.
        Each profession defines its own weight profile.
        """
        weights = self._get_weights(profession_slug)
        score = 0.0
        for metric, weight in weights.items():
            before = metrics_before.get(metric, 0)
            after = metrics_after.get(metric, 0)
            delta = after - before
            score += delta * weight

        return round(max(0.0, score), 2)

    def compute_final_score(self, metrics: dict[str, float], profession_slug: str) -> float:
        """
        Final scenario score = weighted sum of final metric values.
        Normalised to 0–100.
        """
        weights = self._get_weights(profession_slug)
        total_weight = sum(weights.values()) or 1.0
        score = sum(metrics.get(k, 0) * w for k, w in weights.items())
        return round(min(100.0, score / total_weight), 2)

    def level_for_xp(self, total_xp: int) -> int:
        level = 1
        for i, threshold in enumerate(self.XP_THRESHOLDS):
            if total_xp >= threshold:
                level = i + 1
        return min(level, len(self.XP_THRESHOLDS))

    def xp_to_next_level(self, current_xp: int, current_level: int) -> int:
        if current_level >= len(self.XP_THRESHOLDS):
            return 0
        return self.XP_THRESHOLDS[current_level] - current_xp

    # ── Profession weight profiles ────────────────────────

    _WEIGHT_PROFILES: dict[str, dict[str, float]] = {
        "software_engineer": {
            "reputation": 0.35,
            "risk": -0.30,        # negative weight: lower risk = better
            "team_morale": 0.20,
            "score": 0.15,
        },
        "doctor": {
            "patient_stability": 0.40,
            "diagnosis_accuracy": 0.30,
            "team_trust": 0.20,
            "score": 0.10,
        },
        "lawyer": {
            "case_strength": 0.35,
            "client_trust": 0.30,
            "court_reputation": 0.25,
            "score": 0.10,
        },
        "business_manager": {
            "company_health": 0.35,
            "stakeholder_trust": 0.25,
            "team_morale": 0.25,
            "score": 0.15,
        },
    }
    _DEFAULT_WEIGHTS = {"reputation": 0.5, "risk": -0.3, "score": 0.2}

    def _get_weights(self, profession_slug: str) -> dict[str, float]:
        return self._WEIGHT_PROFILES.get(profession_slug, self._DEFAULT_WEIGHTS)
