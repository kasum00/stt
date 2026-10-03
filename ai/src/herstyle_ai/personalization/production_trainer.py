import json

from datetime import (
    datetime,
    timezone,
)

from pathlib import Path

from herstyle_ai.personalization.training_guard import (
    PersonalizationTrainingGuard,
)

from herstyle_ai.personalization.temporal_split import (
    chronological_split,
)

from herstyle_ai.personalization.learned_ranker import (
    LearnedPersonalizationRanker,
)

from herstyle_ai.personalization.learned_ranker_evaluator import (
    LearnedRankerEvaluator,
)

from herstyle_ai.personalization.learned_model_artifact import (
    LearnedPersonalizationModelArtifact,
)


class ProductionPersonalizationTrainer:

    def __init__(
        self,
        project_root,
        *,
        train_ratio=0.8,
    ):

        self.project_root = Path(
            project_root
        )

        self.train_ratio = float(
            train_ratio
        )

        if not 0.0 < self.train_ratio < 1.0:

            raise ValueError(
                "train_ratio must be between 0 and 1"
            )

        self.guard = (
            PersonalizationTrainingGuard(
                project_root=self.project_root
            )
        )

        self.evaluator = (
            LearnedRankerEvaluator()
        )

        self.artifact = (
            LearnedPersonalizationModelArtifact(
                project_root=self.project_root
            )
        )

    @staticmethod
    def _load_dataset(
        dataset_path,
    ):

        rows = []

        with Path(
            dataset_path
        ).open(
            "r",
            encoding="utf-8",
        ) as f:

            for line_number, line in enumerate(
                f,
                start=1,
            ):

                line = line.strip()

                if not line:

                    continue

                try:

                    row = json.loads(
                        line
                    )

                except json.JSONDecodeError as exc:

                    raise RuntimeError(
                        "Invalid training dataset row "
                        f"at line {line_number}: {exc}"
                    ) from exc

                if not isinstance(
                    row,
                    dict,
                ):

                    raise RuntimeError(
                        "Training dataset row "
                        f"at line {line_number} must be an object"
                    )

                rows.append(
                    row
                )

        return rows

    @staticmethod
    def _require_both_labels(
        rows,
        split_name,
    ):

        labels = {
            int(
                row.get(
                    "label",
                    0,
                )
            )
            for row in rows
        }

        if not {
            0,
            1,
        }.issubset(
            labels
        ):

            raise RuntimeError(
                f"{split_name} split must contain both "
                "positive and negative labels"
            )

    @staticmethod
    def _candidate_version():

        timestamp = datetime.now(
            timezone.utc
        ).strftime(
            "%Y%m%dT%H%M%SZ"
        )

        return (
            "p9-logreg-candidate-"
            + timestamp
        )

    def train(
        self,
    ):

        # =================================================
        # HARD PRODUCTION GUARD
        #
        # This must happen before dataset loading, fitting,
        # candidate creation, or any model overwrite.
        # =================================================
        gate_status = self.guard.require_ready()

        rows = self._load_dataset(
            gate_status[
                "dataset_path"
            ]
        )

        train_rows, test_rows = chronological_split(
            rows,
            train_ratio=self.train_ratio,
        )

        self._require_both_labels(
            train_rows,
            "training",
        )

        self._require_both_labels(
            test_rows,
            "test",
        )

        ranker = (
            LearnedPersonalizationRanker()
        )

        ranker.fit(
            train_rows
        )

        metrics = self.evaluator.evaluate(
            ranker,
            test_rows,
        )

        version = self._candidate_version()

        saved = self.artifact.save(
            ranker=ranker,
            training_rows=train_rows,
            evaluation_metrics=metrics,
            dataset_report=gate_status,
            version=version,
        )

        # Candidate artifacts are never activated by the trainer.
        return {
            "status": "candidate_saved",
            "activated": False,
            "model_version": version,
            "model_path": saved[
                "model_path"
            ],
            "metadata_path": saved[
                "metadata_path"
            ],
            "metadata": saved[
                "metadata"
            ],
            "train_examples": len(
                train_rows
            ),
            "test_examples": len(
                test_rows
            ),
            "evaluation": metrics,
        }


__all__ = [
    "ProductionPersonalizationTrainer",
]
