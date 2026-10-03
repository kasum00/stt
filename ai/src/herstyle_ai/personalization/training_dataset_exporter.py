import json

from collections import (
    Counter,
    defaultdict,
)

from pathlib import Path

from typing import (
    Any,
    Iterable,
    Mapping,
    Optional,
)

from herstyle_ai.personalization.training_example_builder import (
    OUTFIT_EVENT_TARGETS,
    PersonalizationTrainingExampleBuilder,
)


# =========================================================
# INITIAL ENGINEERING GATE
#
# These are conservative project thresholds,
# not universal statistical laws.
# =========================================================

MIN_TRAIN_EXAMPLES = 100

MIN_POSITIVE = 30

MIN_NEGATIVE = 30

MIN_EXAMPLES_PER_USER = 50

MIN_POSITIVE_PER_USER = 15

MIN_NEGATIVE_PER_USER = 15


class PersonalizationTrainingDatasetExporter:

    def __init__(
        self,
        project_root,
        *,
        excluded_user_prefixes=(
            "test_",
            "p9_",
        ),
        dataset_filename=(
            "training_dataset.jsonl"
        ),
        report_filename=(
            "training_dataset_report.json"
        ),
    ):

        self.project_root = Path(
            project_root
        )

        self.data_dir = (
            self.project_root
            / "data"
            / "processed"
            / "personalization"
        )

        self.data_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.dataset_path = (
            self.data_dir
            / dataset_filename
        )

        self.report_path = (
            self.data_dir
            / report_filename
        )

        self.excluded_user_prefixes = tuple(
            str(prefix)
            for prefix in (
                excluded_user_prefixes
                or ()
            )
        )

    @staticmethod
    def _event_to_dict(
        event: Any,
    ) -> dict[str, Any]:

        if isinstance(
            event,
            Mapping,
        ):

            return dict(
                event
            )

        if hasattr(
            event,
            "to_dict",
        ):

            payload = event.to_dict()

            if isinstance(
                payload,
                Mapping,
            ):

                return dict(
                    payload
                )

        raise TypeError(
            "events must be mappings or dataclass-like feedback events"
        )

    @staticmethod
    def _user_id(
        event: Mapping[str, Any],
    ) -> str:

        return str(
            event.get(
                "user_id",
                "default",
            )
        )

    @staticmethod
    def _recommendation_id(
        event: Mapping[str, Any],
    ) -> Optional[str]:

        direct_id = event.get(
            "recommendation_id"
        )

        if direct_id:

            return str(
                direct_id
            )

        metadata = event.get(
            "metadata",
            {},
        )

        if not isinstance(
            metadata,
            Mapping,
        ):

            return None

        metadata_id = metadata.get(
            "recommendation_id"
        )

        if metadata_id:

            return str(
                metadata_id
            )

        snapshot = metadata.get(
            "training_snapshot"
        )

        if not isinstance(
            snapshot,
            Mapping,
        ):

            return None

        snapshot_id = snapshot.get(
            "recommendation_id"
        )

        if snapshot_id:

            return str(
                snapshot_id
            )

        return None

    def _is_excluded_user(
        self,
        user_id: str,
    ) -> bool:

        return any(
            user_id.startswith(
                prefix
            )
            for prefix in self.excluded_user_prefixes
        )

    @staticmethod
    def _dedup_key(
        example: Mapping[str, Any],
    ):

        return (
            str(
                example.get(
                    "user_id"
                )
            ),
            str(
                example.get(
                    "recommendation_id"
                )
            ),
            str(
                example.get(
                    "event_type"
                )
            ),
        )

    @staticmethod
    def _unique_strings(
        values,
    ):

        result = []

        for value in values:

            if value is None:

                continue

            value = str(
                value
            )

            if value not in result:

                result.append(
                    value
                )

        return result

    def _append_evidence(
        self,
        row: dict[str, Any],
        event: Mapping[str, Any],
    ):

        event_type = event.get(
            "event_type"
        )

        evidence_event_types = row.setdefault(
            "evidence_event_types",
            [],
        )

        row[
            "evidence_event_types"
        ] = self._unique_strings(
            [
                *evidence_event_types,
                event_type,
            ]
        )

        event_id = event.get(
            "event_id"
        )

        evidence_event_ids = row.setdefault(
            "evidence_event_ids",
            [],
        )

        row[
            "evidence_event_ids"
        ] = self._unique_strings(
            [
                *evidence_event_ids,
                event_id,
            ]
        )

        row[
            "evidence_count"
        ] = int(
            row.get(
                "evidence_count",
                0,
            )
        ) + 1

    def _quality_report(
        self,
        dataset: list[dict[str, Any]],
    ) -> dict[str, Any]:

        labels = Counter(
            int(
                row.get(
                    "label",
                    0,
                )
            )
            for row in dataset
        )

        positive = int(
            labels.get(
                1,
                0,
            )
        )

        negative = int(
            labels.get(
                0,
                0,
            )
        )

        by_user = defaultdict(
            Counter
        )

        for row in dataset:

            user_id = str(
                row.get(
                    "user_id"
                )
            )

            by_user[
                user_id
            ][
                "examples"
            ] += 1

            by_user[
                user_id
            ][
                "positive"
            ] += int(
                row.get(
                    "label"
                ) == 1
            )

            by_user[
                user_id
            ][
                "negative"
            ] += int(
                row.get(
                    "label"
                ) == 0
            )

        blockers = []

        if len(
            dataset
        ) < MIN_TRAIN_EXAMPLES:

            blockers.append(
                "train_examples_below_minimum"
            )

        if positive < MIN_POSITIVE:

            blockers.append(
                "positive_examples_below_minimum"
            )

        if negative < MIN_NEGATIVE:

            blockers.append(
                "negative_examples_below_minimum"
            )

        for user_id, counts in sorted(
            by_user.items()
        ):

            if counts[
                "examples"
            ] < MIN_EXAMPLES_PER_USER:

                blockers.append(
                    f"user:{user_id}:examples_below_minimum"
                )

            if counts[
                "positive"
            ] < MIN_POSITIVE_PER_USER:

                blockers.append(
                    f"user:{user_id}:positive_below_minimum"
                )

            if counts[
                "negative"
            ] < MIN_NEGATIVE_PER_USER:

                blockers.append(
                    f"user:{user_id}:negative_below_minimum"
                )

        per_user = {
            user_id: dict(
                counts
            )
            for user_id, counts in sorted(
                by_user.items()
            )
        }

        return {
            "train_ready_examples": len(
                dataset
            ),
            "positive": positive,
            "negative": negative,
            "users": len(
                per_user
            ),
            "per_user": per_user,
            "ready_to_train": not blockers,
            "blockers": blockers,
            "thresholds": {
                "min_train_examples": MIN_TRAIN_EXAMPLES,
                "min_positive": MIN_POSITIVE,
                "min_negative": MIN_NEGATIVE,
                "min_examples_per_user": MIN_EXAMPLES_PER_USER,
                "min_positive_per_user": MIN_POSITIVE_PER_USER,
                "min_negative_per_user": MIN_NEGATIVE_PER_USER,
            },
        }

    def build(
        self,
        events: Iterable[Any],
        item_lookup=None,
    ):

        event_dicts = [
            self._event_to_dict(
                event
            )
            for event in events
        ]

        eligible_events = []

        report = {
            "total_events": len(
                event_dicts
            ),
            "legacy_without_recommendation": 0,
            "excluded_test_user": 0,
            "excluded_non_outfit_event": 0,
            "duplicate_events_collapsed": 0,
        }

        for event in event_dicts:

            if event.get(
                "event_type"
            ) not in OUTFIT_EVENT_TARGETS:

                report[
                    "excluded_non_outfit_event"
                ] += 1

                continue

            user_id = self._user_id(
                event
            )

            if self._is_excluded_user(
                user_id
            ):

                report[
                    "excluded_test_user"
                ] += 1

                continue

            if self._recommendation_id(
                event
            ) is None:

                report[
                    "legacy_without_recommendation"
                ] += 1

                continue

            eligible_events.append(
                event
            )

        builder = PersonalizationTrainingExampleBuilder(
            item_lookup=item_lookup
        )

        examples = builder.build(
            eligible_events
        )

        dataset_by_key = {}

        for example, event in zip(
            examples,
            eligible_events,
        ):

            row = example.to_dict()

            recommendation_id = self._recommendation_id(
                event
            )

            if row.get(
                "recommendation_id"
            ) is None:

                row[
                    "recommendation_id"
                ] = recommendation_id

            key = self._dedup_key(
                row
            )

            if key in dataset_by_key:

                report[
                    "duplicate_events_collapsed"
                ] += 1

                self._append_evidence(
                    dataset_by_key[
                        key
                    ],
                    event,
                )

                continue

            row[
                "evidence_event_types"
            ] = []

            row[
                "evidence_event_ids"
            ] = []

            row[
                "evidence_count"
            ] = 0

            self._append_evidence(
                row,
                event,
            )

            dataset_by_key[
                key
            ] = row

        dataset = list(
            dataset_by_key.values()
        )

        quality = self._quality_report(
            dataset
        )

        report.update(
            quality
        )

        report[
            "eligible_snapshot_events"
        ] = len(
            eligible_events
        )

        return dataset, report

    def export(
        self,
        events: Iterable[Any],
        item_lookup=None,
    ):

        dataset, report = self.build(
            events=events,
            item_lookup=item_lookup,
        )

        with self.dataset_path.open(
            "w",
            encoding="utf-8",
        ) as f:

            for row in dataset:

                f.write(
                    json.dumps(
                        row,
                        ensure_ascii=False,
                        separators=(
                            ",",
                            ":",
                        ),
                    )
                )

                f.write(
                    "\n"
                )

        with self.report_path.open(
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                report,
                f,
                ensure_ascii=False,
                indent=2,
            )

            f.write(
                "\n"
            )

        return {
            "dataset": dataset,
            "report": report,
            "dataset_path": str(
                self.dataset_path
            ),
            "report_path": str(
                self.report_path
            ),
        }


__all__ = [
    "MIN_TRAIN_EXAMPLES",
    "MIN_POSITIVE",
    "MIN_NEGATIVE",
    "MIN_EXAMPLES_PER_USER",
    "MIN_POSITIVE_PER_USER",
    "MIN_NEGATIVE_PER_USER",
    "PersonalizationTrainingDatasetExporter",
]
