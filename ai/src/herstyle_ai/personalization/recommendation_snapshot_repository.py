import json

from datetime import (
    datetime,
    timezone,
)

from pathlib import Path


class RecommendationSnapshotRepository:

    def __init__(
        self,
        project_root,
        data_root=None,
    ):

        self.project_root = Path(
            project_root
        )
        self.data_root = Path(data_root) if data_root is not None else self.project_root / "data"

        self.data_dir = (
            self.data_root
            / "processed"
            / "personalization"
        )

        self.data_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.path = (
            self.data_dir
            / "recommendation_snapshots.jsonl"
        )

    @staticmethod
    def _now():

        return datetime.now(
            timezone.utc
        ).isoformat()

    def add(
        self,
        snapshot,
    ):

        if not isinstance(
            snapshot,
            dict,
        ):

            raise TypeError(
                "snapshot must be a dict"
            )

        recommendation_id = snapshot.get(
            "recommendation_id"
        )

        if not recommendation_id:

            raise ValueError(
                "recommendation_id is required"
            )

        record = dict(
            snapshot
        )

        record.setdefault(
            "created_at",
            self._now(),
        )

        with self.path.open(
            "a",
            encoding="utf-8",
        ) as f:

            json.dump(
                record,
                f,
                ensure_ascii=False,
            )

            f.write(
                "\n"
            )

        return record

    def get(
        self,
        recommendation_id,
    ):

        if not self.path.exists():

            return None

        recommendation_id = str(
            recommendation_id
        )

        found = None

        with self.path.open(
            "r",
            encoding="utf-8",
        ) as f:

            for line in f:

                line = line.strip()

                if not line:

                    continue

                try:

                    record = json.loads(
                        line
                    )

                except (
                    json.JSONDecodeError,
                    TypeError,
                ):

                    continue

                if str(
                    record.get(
                        "recommendation_id"
                    )
                ) == recommendation_id:

                    found = record

        return found

    def list_all(
        self,
        user_id=None,
    ):

        if not self.path.exists():

            return []

        records = []

        with self.path.open(
            "r",
            encoding="utf-8",
        ) as f:

            for line in f:

                line = line.strip()

                if not line:

                    continue

                try:

                    record = json.loads(
                        line
                    )

                except (
                    json.JSONDecodeError,
                    TypeError,
                ):

                    continue

                if (
                    user_id is not None
                    and str(
                        record.get(
                            "user_id"
                        )
                    )
                    != str(
                        user_id
                    )
                ):

                    continue

                records.append(
                    record
                )

        return records

    def count(
        self,
        user_id=None,
    ):

        return len(
            self.list_all(
                user_id=user_id
            )
        )


__all__ = [
    "RecommendationSnapshotRepository",
]
