from pathlib import Path


# =========================================================
# INITIAL ENGINEERING THRESHOLDS
#
# These are deployment gates for this project.
# They are NOT universal ML quality thresholds.
# =========================================================

MIN_TEST_EXAMPLES = 20

MIN_ROC_AUC = 0.55

MIN_BALANCED_ACCURACY = 0.55

MIN_PAIRWISE_ACCURACY = 0.55

MIN_PR_AUC_MARGIN_OVER_PREVALENCE = 0.02


class PersonalizationCandidateAcceptance:

    def __init__(
        self,
        *,
        min_test_examples=MIN_TEST_EXAMPLES,
        min_roc_auc=MIN_ROC_AUC,
        min_balanced_accuracy=MIN_BALANCED_ACCURACY,
        min_pairwise_accuracy=MIN_PAIRWISE_ACCURACY,
        min_pr_auc_margin=MIN_PR_AUC_MARGIN_OVER_PREVALENCE,
    ):

        self.min_test_examples = int(
            min_test_examples
        )

        self.min_roc_auc = float(
            min_roc_auc
        )

        self.min_balanced_accuracy = float(
            min_balanced_accuracy
        )

        self.min_pairwise_accuracy = float(
            min_pairwise_accuracy
        )

        self.min_pr_auc_margin = float(
            min_pr_auc_margin
        )

    @staticmethod
    def _optional_float(
        metrics,
        key,
    ):

        value = metrics.get(
            key
        )

        if value is None:

            return None

        try:

            return float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return None

    def thresholds(self):

        return {
            "min_test_examples": self.min_test_examples,
            "min_roc_auc": self.min_roc_auc,
            "min_balanced_accuracy": self.min_balanced_accuracy,
            "min_pairwise_accuracy": self.min_pairwise_accuracy,
            "min_pr_auc_margin": self.min_pr_auc_margin,
        }

    def evaluate(
        self,
        metrics,
    ):

        if not isinstance(
            metrics,
            dict,
        ):

            metrics = {}

        examples = int(
            metrics.get(
                "examples",
                metrics.get(
                    "test_examples",
                    0,
                ),
            )
            or 0
        )

        positive = int(
            metrics.get(
                "positive",
                0,
            )
            or 0
        )

        negative = int(
            metrics.get(
                "negative",
                0,
            )
            or 0
        )

        prevalence = (
            positive / examples
            if examples > 0
            else 0.0
        )

        required_pr_auc = (
            prevalence
            + self.min_pr_auc_margin
        )

        roc_auc = self._optional_float(
            metrics,
            "roc_auc",
        )

        pr_auc = self._optional_float(
            metrics,
            "pr_auc",
        )

        balanced_accuracy = self._optional_float(
            metrics,
            "balanced_accuracy",
        )

        pairwise_accuracy = self._optional_float(
            metrics,
            "pairwise_accuracy",
        )

        blockers = []

        if examples < self.min_test_examples:

            blockers.append(
                "test_examples_below_minimum"
            )

        if roc_auc is None or roc_auc < self.min_roc_auc:

            blockers.append(
                "roc_auc_below_minimum"
            )

        if balanced_accuracy is None or balanced_accuracy < self.min_balanced_accuracy:

            blockers.append(
                "balanced_accuracy_below_minimum"
            )

        if pairwise_accuracy is None or pairwise_accuracy < self.min_pairwise_accuracy:

            blockers.append(
                "pairwise_accuracy_below_minimum"
            )

        if pr_auc is None or pr_auc < required_pr_auc:

            blockers.append(
                "pr_auc_below_prevalence_margin"
            )

        return {
            "accepted": not blockers,
            "blockers": blockers,
            "metrics": dict(
                metrics
            ),
            "test_examples": examples,
            "positive": positive,
            "negative": negative,
            "positive_prevalence": prevalence,
            "required_pr_auc": required_pr_auc,
            "thresholds": self.thresholds(),
        }

    def accept(
        self,
        metrics,
    ):

        return bool(
            self.evaluate(
                metrics
            )["accepted"]
        )

    def require_accepted(
        self,
        metrics,
    ):

        decision = self.evaluate(
            metrics
        )

        if not decision[
            "accepted"
        ]:

            raise RuntimeError(
                "Personalization candidate rejected: "
                + ", ".join(
                    decision[
                        "blockers"
                    ]
                )
            )

        return decision


__all__ = [
    "MIN_TEST_EXAMPLES",
    "MIN_ROC_AUC",
    "MIN_BALANCED_ACCURACY",
    "MIN_PAIRWISE_ACCURACY",
    "MIN_PR_AUC_MARGIN_OVER_PREVALENCE",
    "PersonalizationCandidateAcceptance",
]
