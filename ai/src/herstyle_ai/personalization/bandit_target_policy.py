class GreedyLoggedCandidateTargetPolicy:

    def __init__(
        self,
        *,
        score_field="scheduler_adjusted_score",
    ):

        self.score_field = str(
            score_field
        )

    def selected_probability(
        self,
        row,
    ):

        candidate_set = (
            row.get(
                "candidate_set"
            )
            or []
        )

        selected_action_id = (
            row.get(
                "selected_action_id"
            )
        )

        behavior_policy = (
            row.get(
                "behavior_policy"
            )
            or {}
        )

        support_action_ids = set(
            behavior_policy.get(
                "support_action_ids"
            )
            or []
        )

        if (
            not candidate_set
            or not selected_action_id
            or not support_action_ids
        ):

            return 0.0

        valid = []

        for candidate in candidate_set:

            action_id = (
                candidate.get(
                    "action_id"
                )
            )

            # Target policy must remain inside
            # behavior-policy support.
            if (
                action_id
                not in support_action_ids
            ):

                continue

            score = (
                candidate.get(
                    self.score_field
                )
            )

            if score is None:

                continue

            try:

                score = float(
                    score
                )

            except (
                TypeError,
                ValueError,
            ):

                continue

            valid.append(
                (
                    action_id,
                    score,
                )
            )

        if not valid:

            return 0.0

        valid.sort(
            key=lambda pair:
                pair[
                    1
                ],
            reverse=True,
        )

        greedy_action_id = (
            valid[
                0
            ][0]
        )

        return (
            1.0
            if (
                greedy_action_id
                == selected_action_id
            )
            else 0.0
        )


__all__ = [
    "GreedyLoggedCandidateTargetPolicy",
]
