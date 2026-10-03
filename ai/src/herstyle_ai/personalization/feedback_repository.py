import json

from pathlib import Path

from typing import (
    Dict,
    Iterator,
    Any,
    Optional,
)

from herstyle_ai.personalization.feedback_models import (
    FeedbackEvent,
)


# =========================================================
# FEEDBACK REPOSITORY
# =========================================================

class FeedbackRepository:

    def __init__(
        self,
        project_root: Path,
        data_root: Path | None = None,
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

        self.feedback_path = (
            self.data_dir
            / "feedback_events.jsonl"
        )

    # =====================================================
    # WRITE
    # =====================================================

    def add(
        self,
        event: FeedbackEvent,
    ) -> Dict[str, Any]:

        if not isinstance(
            event,
            FeedbackEvent,
        ):

            raise TypeError(
                "event must be a FeedbackEvent"
            )

        payload = event.to_dict()

        with self.feedback_path.open(
            "a",
            encoding="utf-8",
        ) as f:

            json.dump(
                payload,
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

        return payload

    # =====================================================
    # READ
    # =====================================================

    def iter_events(
        self,
    ) -> Iterator[Dict[str, Any]]:

        if not self.feedback_path.exists():

            return

        with self.feedback_path.open(
            "r",
            encoding="utf-8",
        ) as f:

            for line in f:

                line = line.strip()

                if not line:

                    continue

                yield json.loads(
                    line
                )

    def read_all(
        self,
    ):

        return list(
            self.iter_events()
        )

    def list_all(
        self,
        user_id: Optional[str] = None,
    ):

        events = self.read_all()

        if user_id is None:

            return events

        return [

            event

            for event in events

            if event.get(
                "user_id"
            ) == user_id
        ]

    def count(
        self,
    ):

        return sum(
            1
            for _ in self.iter_events()
        )
