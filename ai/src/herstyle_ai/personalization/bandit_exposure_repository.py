import json

from pathlib import Path


class BanditExposureRepository:

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
            / "bandit"
        )

        self.data_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.path = (
            self.data_dir
            / "decision_exposures.jsonl"
        )

    # =====================================================
    # READ
    # =====================================================

    def list_all(
        self,
        user_id=None,
    ):

        if not self.path.exists():

            return []

        rows = []

        with self.path.open(
            "r",
            encoding="utf-8",
        ) as f:

            for line in f:

                line = line.strip()

                if not line:
                    continue

                row = json.loads(
                    line
                )

                if (
                    user_id is not None
                    and str(
                        row.get(
                            "user_id"
                        )
                    )
                    != str(
                        user_id
                    )
                ):

                    continue

                rows.append(
                    row
                )

        return rows

    # =====================================================
    # FIND
    # =====================================================

    def get_by_recommendation_id(
        self,
        recommendation_id,
    ):

        recommendation_id = str(
            recommendation_id
        )

        for row in reversed(
            self.list_all()
        ):

            if (
                str(
                    row.get(
                        "recommendation_id"
                    )
                )
                == recommendation_id
            ):

                return row

        return None

    def get_by_decision_id(
        self,
        decision_id,
    ):

        decision_id = str(
            decision_id
        )

        for row in reversed(
            self.list_all()
        ):

            if (
                str(
                    row.get(
                        "decision_id"
                    )
                )
                == decision_id
            ):

                return row

        return None

    # =====================================================
    # WRITE
    # =====================================================

    def add(
        self,
        exposure,
    ):

        if not isinstance(
            exposure,
            dict,
        ):

            raise TypeError(
                "exposure must be dict"
            )

        decision_id = (
            exposure.get(
                "decision_id"
            )
        )

        recommendation_id = (
            exposure.get(
                "recommendation_id"
            )
        )

        if not decision_id:

            raise ValueError(
                "decision_id is required"
            )

        if not recommendation_id:

            raise ValueError(
                "recommendation_id is required"
            )

        existing = (
            self.get_by_recommendation_id(
                recommendation_id
            )
        )

        if existing is not None:

            return existing

        with self.path.open(
            "a",
            encoding="utf-8",
        ) as f:

            json.dump(
                exposure,
                f,
                ensure_ascii=False,
                separators=(
                    ",",
                    ":",
                ),
            )

            f.write(
                "\n"
            )

        return exposure

    def count(
        self,
    ):

        return len(
            self.list_all()
        )


__all__ = [
    "BanditExposureRepository",
]
