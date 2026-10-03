from pathlib import Path

import joblib

import numpy as np

from sklearn.feature_extraction import (
    DictVectorizer,
)

from sklearn.linear_model import (
    LogisticRegression,
)

from herstyle_ai.personalization.learned_feature_builder import (
    LearnedPersonalizationFeatureBuilder,
)


class LearnedPersonalizationRanker:

    def __init__(
        self,
    ):

        self.feature_builder = (
            LearnedPersonalizationFeatureBuilder()
        )

        self.vectorizer = (
            DictVectorizer(
                sparse=True
            )
        )

        self.model = (
            LogisticRegression(
                max_iter=1000,
                solver="lbfgs",
            )
        )

        self.is_fitted = False

    def fit(
        self,
        rows,
    ):

        rows = list(
            rows
        )

        if not rows:

            raise ValueError(
                "Cannot fit learned ranker with no rows"
            )

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

        if len(
            np.unique(
                labels
            )
        ) < 2:

            raise ValueError(
                "Learned ranker requires both positive and negative labels"
            )

        feature_rows = (
            self.feature_builder
            .build_many(
                rows
            )
        )

        matrix = (
            self.vectorizer
            .fit_transform(
                feature_rows
            )
        )

        sample_weight = np.asarray(
            [
                self._safe_sample_weight(
                    row.get(
                        "sample_weight",
                        1.0,
                    )
                )
                for row in rows
            ],
            dtype=float,
        )

        self.model.fit(
            matrix,
            labels,
            sample_weight=sample_weight,
        )

        self.is_fitted = True

        return self

    @staticmethod
    def _safe_sample_weight(
        value,
    ):

        try:

            value = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return 1.0

        if not np.isfinite(
            value
        ) or value <= 0.0:

            return 1.0

        return value

    def _require_fitted(
        self,
    ):

        if not self.is_fitted:

            raise RuntimeError(
                "Learned personalization ranker is not fitted"
            )

    def score_one(
        self,
        row,
    ):
        """Return learned_preference_score in the range [0, 1].

        This is a model score from Logistic Regression.  It is not a
        calibrated probability that a user will like an outfit.
        """

        self._require_fitted()

        features = self.feature_builder.build(
            row
        )

        matrix = self.vectorizer.transform(
            [
                features
            ]
        )

        score = self.model.predict_proba(
            matrix
        )[0, 1]

        return float(
            min(
                1.0,
                max(
                    0.0,
                    score,
                ),
            )
        )

    def score_many(
        self,
        rows,
    ):

        self._require_fitted()

        rows = list(
            rows
        )

        if not rows:

            return []

        feature_rows = (
            self.feature_builder
            .build_many(
                rows
            )
        )

        matrix = self.vectorizer.transform(
            feature_rows
        )

        scores = self.model.predict_proba(
            matrix
        )[:, 1]

        return [
            float(
                min(
                    1.0,
                    max(
                        0.0,
                        score,
                    ),
                )
            )
            for score in scores
        ]

    def save(
        self,
        path,
    ):

        self._require_fitted()

        path = Path(
            path
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        joblib.dump(
            {
                "vectorizer": self.vectorizer,
                "model": self.model,
                "feature_builder": self.feature_builder,
            },
            path,
        )

        return path

    @classmethod
    def load(
        cls,
        path,
    ):

        payload = joblib.load(
            Path(
                path
            )
        )

        ranker = cls()

        ranker.vectorizer = payload[
            "vectorizer"
        ]

        ranker.model = payload[
            "model"
        ]

        ranker.feature_builder = payload.get(
            "feature_builder",
            LearnedPersonalizationFeatureBuilder(),
        )

        ranker.is_fitted = True

        return ranker


__all__ = [
    "LearnedPersonalizationRanker",
]
