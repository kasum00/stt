import os

from herstyle_ai.personalization.bandit_exposure import (
    stable_action_id,
)

from herstyle_ai.personalization.bandit_policy import (
    EpsilonGreedyBanditPolicy,
)

from herstyle_ai.personalization.bandit_activation_guard import (
    BanditExplorationGuard,
)


def _env_bool(name, default=False):

    value = os.getenv(name)

    if value is None:
        return bool(default)

    return str(value).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _safe_float(value):

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class SafeBanditRuntime:

    MAX_EPSILON = 0.05
    MAX_POOL_SIZE = 3
    MAX_SCORE_DROP = 0.08

    def __init__(
        self,
        *,
        enabled=None,
        epsilon=None,
        max_explore_candidates=None,
        max_score_drop=None,
        random_seed=None,
    ):

        if enabled is None:
            enabled = _env_bool(
                "HERSTYLE_BANDIT_EXPLORATION_ENABLED",
                False,
            )

        if epsilon is None:
            epsilon = os.getenv(
                "HERSTYLE_BANDIT_EPSILON",
                "0.02",
            )

        requested_epsilon = _safe_float(epsilon)

        if max_explore_candidates is None:
            max_explore_candidates = os.getenv(
                "HERSTYLE_BANDIT_MAX_CANDIDATES",
                "3",
            )

        if max_score_drop is None:
            max_score_drop = os.getenv(
                "HERSTYLE_BANDIT_MAX_SCORE_DROP",
                "0.08",
            )

        try:
            requested_candidates = int(
                max_explore_candidates
            )
        except (TypeError, ValueError):
            requested_candidates = 1

        requested_score_drop = _safe_float(
            max_score_drop
        )

        if requested_score_drop is None:
            requested_score_drop = 0.0

        self.guard = BanditExplorationGuard(
            max_epsilon=self.MAX_EPSILON
        )
        self.activation_status = self.guard.check(
            epsilon=requested_epsilon,
            enabled=enabled,
        )
        self.enabled = bool(
            self.activation_status["allowed"]
        )

        self.epsilon = min(
            max(
                requested_epsilon
                if requested_epsilon is not None
                else 0.0,
                0.0,
            ),
            self.MAX_EPSILON,
        )

        self.max_explore_candidates = min(
            max(requested_candidates, 1),
            self.MAX_POOL_SIZE,
        )

        self.max_score_drop = min(
            max(requested_score_drop, 0.0),
            self.MAX_SCORE_DROP,
        )

        self.policy = EpsilonGreedyBanditPolicy(
            epsilon=self.epsilon,
            max_explore_candidates=(
                self.max_explore_candidates
            ),
            max_score_drop=self.max_score_drop,
            random_seed=random_seed,
        )

    @staticmethod
    def _score(candidate):

        scheduler = candidate.get("scheduler") or {}
        value = scheduler.get("adjusted_score")

        if value is None:
            value = candidate.get("score", 0.0)

        return float(value)

    def _deterministic(self, candidates, *, reason):

        candidates = list(candidates)

        if not candidates:
            return {
                "selected": None,
                "selected_action_id": None,
                "selected_propensity": None,
                "action_probabilities": {},
                "behavior_policy": {
                    "name":
                        "herstyle-ranking-scheduler",
                    "version": "p10-deterministic-v2",
                    "deterministic": True,
                    "exploration_enabled": False,
                    "ips_eligible": False,
                    "reason": reason,
                },
            }

        ordered = sorted(
            candidates,
            key=self._score,
            reverse=True,
        )
        selected = ordered[0]
        action_id = stable_action_id(selected)
        probabilities = {action_id: 1.0}

        return {
            "selected": selected,
            "selected_action_id": action_id,
            "selected_propensity": 1.0,
            "action_probabilities": probabilities,
            "behavior_policy": {
                "name":
                    "herstyle-ranking-scheduler",
                "version": "p10-deterministic-v2",
                "deterministic": True,
                "exploration_enabled": False,
                "selected_propensity": 1.0,
                "ips_eligible": False,
                "support_action_ids": [action_id],
                "action_probabilities": probabilities,
                "reason": reason,
            },
        }

    def choose(self, candidates):

        candidates = list(candidates)

        if not candidates:
            return self._deterministic(
                [],
                reason="no_candidates",
            )

        if not self.enabled:
            blockers = (
                self.activation_status.get(
                    "blockers"
                )
                or []
            )
            reason = "exploration_disabled"

            if blockers:
                reason = (
                    "exploration_guard_blocked:"
                    + ",".join(blockers)
                )

            return self._deterministic(
                candidates,
                reason=reason,
            )

        decision = self.policy.choose(candidates)

        if decision.get("selected") is None:
            return self._deterministic(
                candidates,
                reason="no_safe_exploration_pool",
            )

        return decision


__all__ = [
    "SafeBanditRuntime",
]
