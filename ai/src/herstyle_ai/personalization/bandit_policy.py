import random

from herstyle_ai.personalization.bandit_exposure import (
    stable_action_id,
)


class EpsilonGreedyBanditPolicy:

    def __init__(
        self,
        *,
        epsilon=0.02,
        max_explore_candidates=3,
        max_score_drop=0.08,
        random_seed=None,
    ):

        self.epsilon = float(epsilon)
        self.max_explore_candidates = int(
            max_explore_candidates
        )
        self.max_score_drop = float(max_score_drop)

        if not 0.0 <= self.epsilon <= 1.0:
            raise ValueError("epsilon must be in [0, 1]")

        if self.max_explore_candidates <= 0:
            raise ValueError(
                "max_explore_candidates must be > 0"
            )

        if self.max_score_drop < 0.0:
            raise ValueError(
                "max_score_drop must be >= 0"
            )

        self.random = random.Random(random_seed)

    @staticmethod
    def _score(candidate):

        scheduler = candidate.get("scheduler") or {}
        value = scheduler.get("adjusted_score")

        if value is None:
            value = candidate.get("score", 0.0)

        return float(value)

    def _pool(self, candidates):

        eligible = [
            candidate
            for candidate in candidates
            if candidate.get("threshold_flag") is not False
        ]

        eligible.sort(
            key=self._score,
            reverse=True,
        )

        if not eligible:
            return []

        best_score = self._score(eligible[0])

        quality_safe = [
            candidate
            for candidate in eligible
            if best_score - self._score(candidate)
            <= self.max_score_drop
        ]

        return quality_safe[:self.max_explore_candidates]

    def distribution(self, candidates):

        pool = self._pool(candidates)

        if not pool:
            return []

        k = len(pool)

        if k == 1 or self.epsilon == 0.0:
            probabilities = [1.0]
        else:
            explore_probability = self.epsilon / k
            probabilities = [
                explore_probability
                for _ in range(k)
            ]
            probabilities[0] += 1.0 - self.epsilon

        return [
            {
                "candidate": candidate,
                "action_id": stable_action_id(candidate),
                "score": self._score(candidate),
                "probability": float(probability),
            }
            for candidate, probability in zip(
                pool,
                probabilities,
            )
        ]

    def choose(self, candidates):

        distribution = self.distribution(candidates)

        if not distribution:
            return {
                "selected": None,
                "selected_action_id": None,
                "selected_propensity": None,
                "action_probabilities": {},
                "behavior_policy": {
                    "name": "epsilon_greedy_topk",
                    "version": "p10-epsilon-v2",
                    "deterministic": True,
                    "exploration_enabled": False,
                    "ips_eligible": False,
                    "reason": "no_safe_candidates",
                },
            }

        k = len(distribution)
        exploration_enabled = self.epsilon > 0.0 and k > 1

        draw = self.random.random()
        cumulative = 0.0
        selected_index = k - 1

        for index, row in enumerate(distribution):
            cumulative += row["probability"]
            if draw <= cumulative:
                selected_index = index
                break

        chosen = distribution[selected_index]
        probability_map = {
            row["action_id"]: float(row["probability"])
            for row in distribution
        }
        support_action_ids = [
            row["action_id"]
            for row in distribution
            if row["probability"] > 0.0
        ]
        ips_eligible = (
            exploration_enabled
            and len(support_action_ids) >= 2
        )

        return {
            "selected": chosen["candidate"],
            "selected_action_id": chosen["action_id"],
            "selected_propensity": float(
                chosen["probability"]
            ),
            "action_probabilities": probability_map,
            "behavior_policy": {
                "name": "epsilon_greedy_topk",
                "version": "p10-epsilon-v2",
                "deterministic": not exploration_enabled,
                "exploration_enabled": exploration_enabled,
                "epsilon": self.epsilon,
                "candidate_pool_size": k,
                "max_score_drop": self.max_score_drop,
                "selected_propensity": float(
                    chosen["probability"]
                ),
                "ips_eligible": ips_eligible,
                "support_action_ids": support_action_ids,
                "action_probabilities": probability_map,
            },
        }


__all__ = [
    "EpsilonGreedyBanditPolicy",
]
