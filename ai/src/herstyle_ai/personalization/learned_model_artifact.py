import json

from datetime import (
    datetime,
    timezone,
)

from pathlib import Path


MODEL_VERSION = "p9-logreg-v1"


class LearnedPersonalizationModelArtifact:

    def __init__(
        self,
        project_root,
    ):

        self.project_root = Path(
            project_root
        )

        self.model_dir = (
            self.project_root
            / "data"
            / "processed"
            / "personalization"
            / "models"
        )

        self.model_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    @staticmethod
    def _now():

        return datetime.now(
            timezone.utc
        ).isoformat()

    @staticmethod
    def _training_window(
        rows,
    ):

        timestamps = []

        for row in rows:

            if not isinstance(
                row,
                dict,
            ):

                continue

            value = row.get(
                "created_at"
            ) or row.get(
                "timestamp"
            )

            if value:

                timestamps.append(
                    str(
                        value
                    )
                )

        if not timestamps:

            return {
                "start": None,
                "end": None,
            }

        timestamps.sort()

        return {
            "start": timestamps[0],
            "end": timestamps[-1],
        }

    @staticmethod
    def _feature_count(
        ranker,
    ):

        vectorizer = getattr(
            ranker,
            "vectorizer",
            None,
        )

        if vectorizer is None:

            return 0

        vocabulary = getattr(
            vectorizer,
            "vocabulary_",
            None,
        )

        if isinstance(
            vocabulary,
            dict,
        ):

            return len(
                vocabulary
            )

        feature_names = getattr(
            vectorizer,
            "feature_names_",
            None,
        )

        if feature_names is None:

            return 0

        return len(
            feature_names
        )

    @staticmethod
    def _label_counts(
        rows,
    ):

        positive = 0
        negative = 0

        for row in rows:

            label = int(
                row.get(
                    "label",
                    0,
                )
            )

            if label == 1:

                positive += 1

            elif label == 0:

                negative += 1

        return positive, negative

    def save(
        self,
        ranker,
        training_rows,
        evaluation_metrics,
        dataset_report,
        version=MODEL_VERSION,
    ):

        rows = list(
            training_rows
        )

        version = str(
            version
        )

        model_path = (
            self.model_dir
            / f"{version}.joblib"
        )

        metadata_path = (
            self.model_dir
            / f"{version}.metadata.json"
        )

        # LearnedPersonalizationRanker performs its own fitted-state check.
        ranker.save(
            model_path
        )

        positive, negative = self._label_counts(
            rows
        )

        if not isinstance(
            evaluation_metrics,
            dict,
        ):

            evaluation_metrics = {}

        if not isinstance(
            dataset_report,
            dict,
        ):

            dataset_report = {}

        metadata = {
            "model_version": version,
            "artifact_type": "learned_personalization_ranker",
            "model_class": type(
                ranker
            ).__name__,
            "trained_at": self._now(),
            "training_examples": len(
                rows
            ),
            "positive": positive,
            "negative": negative,
            "feature_count": self._feature_count(
                ranker
            ),
            "training_window": self._training_window(
                rows
            ),
            "evaluation": dict(
                evaluation_metrics
            ),
            "dataset_report": dict(
                dataset_report
            ),
        }

        with metadata_path.open(
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                metadata,
                f,
                ensure_ascii=False,
                indent=2,
            )

            f.write(
                "\n"
            )

        return {
            "model_path": str(
                model_path
            ),
            "metadata_path": str(
                metadata_path
            ),
            "metadata": metadata,
        }

    def load_metadata(
        self,
        version=MODEL_VERSION,
    ):

        metadata_path = (
            self.model_dir
            / f"{str(version)}.metadata.json"
        )

        with metadata_path.open(
            "r",
            encoding="utf-8",
        ) as f:

            return json.load(
                f
            )


__all__ = [
    "MODEL_VERSION",
    "LearnedPersonalizationModelArtifact",
]
