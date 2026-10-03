import json

from pathlib import Path


class PersonalizationTrainingGuard:

    def __init__(
        self,
        project_root,
    ):

        self.project_root = Path(
            project_root
        )

        self.training_dir = (
            self.project_root
            / "data"
            / "processed"
            / "personalization"
            / "training"
        )

        # Support the filename currently produced
        # by the exporter.
        self.report_path = (
            self.project_root
            / "data"
            / "processed"
            / "personalization"
            / "training_dataset_report.json"
        )

        self.dataset_path = (
            self.project_root
            / "data"
            / "processed"
            / "personalization"
            / "training_dataset.jsonl"
        )

    def _missing_status(
        self,
        blocker,
    ):

        return {
            "ready": False,
            "blockers": [
                blocker
            ],
            "report_path": str(
                self.report_path
            ),
            "dataset_path": str(
                self.dataset_path
            ),
        }

    def check(
        self,
    ):

        if not self.report_path.is_file():

            return self._missing_status(
                "training_report_missing"
            )

        try:

            with self.report_path.open(
                "r",
                encoding="utf-8",
            ) as f:

                report = json.load(
                    f
                )

        except (
            OSError,
            json.JSONDecodeError,
        ):

            return self._missing_status(
                "training_report_invalid"
            )

        if not isinstance(
            report,
            dict,
        ):

            return self._missing_status(
                "training_report_invalid"
            )

        blockers = report.get(
            "blockers",
            [],
        )

        if not isinstance(
            blockers,
            list,
        ):

            blockers = [
                "training_report_invalid"
            ]

        blockers = [
            str(
                blocker
            )
            for blocker in blockers
            if blocker
        ]

        if not self.dataset_path.is_file():

            blockers.append(
                "training_dataset_missing"
            )

        ready = bool(
            report.get(
                "ready_to_train",
                False,
            )
        ) and not blockers

        status = dict(
            report
        )

        status.update(
            {
                "ready": ready,
                "blockers": blockers,
                "report_path": str(
                    self.report_path
                ),
                "dataset_path": str(
                    self.dataset_path
                ),
            }
        )

        return status

    def require_ready(
        self,
    ):

        status = self.check()

        if status[
            "ready"
        ]:

            return status

        blockers = status.get(
            "blockers",
            [],
        )

        detail = ", ".join(
            str(
                blocker
            )
            for blocker in blockers
        ) or "training_quality_gate_failed"

        raise RuntimeError(
            "Personalization training is not allowed: "
            + detail
        )


__all__ = [
    "PersonalizationTrainingGuard",
]
