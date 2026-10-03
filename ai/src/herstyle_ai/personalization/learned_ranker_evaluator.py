from collections import (
    defaultdict,
)

import numpy as np

from sklearn.metrics import (
    balanced_accuracy_score,
    average_precision_score,
    roc_auc_score,
)


class LearnedRankerEvaluator:

    @staticmethod
    def _binary_predictions(
        scores,
        threshold=0.5,
    ):

        return [
            1
            if float(
                score
            ) >= float(
                threshold
            )
            else 0
            for score in scores
        ]

    @staticmethod
    def _pairwise_accuracy(
        rows,
        scores,
    ):

        by_user = defaultdict(
            lambda: {
                "positive": [],
                "negative": [],
            }
        )

        for row, score in zip(
            rows,
            scores,
        ):

            user_id = str(
                row.get(
                    "user_id",
                    "default",
                )
            )

            label = int(
                row.get(
                    "label",
                    0,
                )
            )

            if label == 1:

                by_user[
                    user_id
                ][
                    "positive"
                ].append(
                    float(
                        score
                    )
                )

            else:

                by_user[
                    user_id
                ][
                    "negative"
                ].append(
                    float(
                        score
                    )
                )

        total_pairs = 0
        correct_pairs = 0.0

        for groups in by_user.values():

            for positive_score in groups[
                "positive"
            ]:

                for negative_score in groups[
                    "negative"
                ]:

                    total_pairs += 1

                    if positive_score > negative_score:

                        correct_pairs += 1.0

                    elif positive_score == negative_score:

                        correct_pairs += 0.5

        if total_pairs == 0:

            return None

        return correct_pairs / total_pairs

    def evaluate(
        self,
        ranker,
        rows,
        threshold=0.5,
    ):

        rows = list(
            rows
        )

        if not rows:

            return {
                "examples": 0,
                "positive": 0,
                "negative": 0,
                "threshold": float(
                    threshold
                ),
                "roc_auc": None,
                "pr_auc": None,
                "balanced_accuracy": None,
                "pairwise_accuracy": None,
            }

        scores = [
            float(
                score
            )
            for score in ranker.score_many(
                rows
            )
        ]

        labels = np.asarray(
            [
                int(
                    row.get(
                        "label",
                        0,
                    )
                )
                for row in rows
            ],
            dtype=int,
        )

        predictions = self._binary_predictions(
            scores,
            threshold=threshold,
        )

        has_both_labels = len(
            np.unique(
                labels
            )
        ) >= 2

        if has_both_labels:

            roc_auc = float(
                roc_auc_score(
                    labels,
                    scores,
                )
            )

            pr_auc = float(
                average_precision_score(
                    labels,
                    scores,
                )
            )

            balanced_accuracy = float(
                balanced_accuracy_score(
                    labels,
                    predictions,
                )
            )

        else:

            roc_auc = None
            pr_auc = None
            balanced_accuracy = None

        return {
            "examples": len(
                rows
            ),
            "positive": int(
                np.sum(
                    labels == 1
                )
            ),
            "negative": int(
                np.sum(
                    labels == 0
                )
            ),
            "threshold": float(
                threshold
            ),
            "roc_auc": roc_auc,
            "pr_auc": pr_auc,
            "balanced_accuracy": balanced_accuracy,
            "pairwise_accuracy": self._pairwise_accuracy(
                rows,
                scores,
            ),
        }


__all__ = [
    "LearnedRankerEvaluator",
]
