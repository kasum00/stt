from datetime import (
    datetime,
    timezone,
)

from typing import (
    Iterable,
    Mapping,
)


def _parse_time(
    value,
):

    if not value:

        return datetime.min

    text = str(
        value
    ).strip()

    if text.endswith(
        "Z"
    ):

        text = (
            text[:-1]
            + "+00:00"
        )

    try:

        parsed = datetime.fromisoformat(
            text
        )

    except ValueError:

        return datetime.min

    # Normalize aware timestamps so that rows with mixed timestamp
    # formats remain sortable.
    if parsed.tzinfo is not None:

        return parsed.astimezone(
            timezone.utc
        ).replace(
            tzinfo=None
        )

    return parsed


def chronological_split(
    rows: Iterable[Mapping],
    train_ratio=0.80,
):
    """Split rows by time without random shuffling.

    ``created_at`` is preferred because it is the training-example field.
    ``timestamp`` is supported for legacy rows.  The original input is not
    mutated and the returned rows are ordered from oldest to newest.
    """

    if not 0.0 < float(
        train_ratio
    ) < 1.0:

        raise ValueError(
            "train_ratio must be between 0 and 1"
        )

    indexed_rows = list(
        enumerate(
            rows
        )
    )

    ordered_rows = sorted(
        indexed_rows,
        key=lambda pair: (
            _parse_time(
                pair[1].get(
                    "created_at"
                )
                or pair[1].get(
                    "timestamp"
                )
            ),
            pair[0],
        ),
    )

    ordered_rows = [
        row
        for _, row in ordered_rows
    ]

    total = len(
        ordered_rows
    )

    if total < 2:

        return ordered_rows, []

    split_index = int(
        total
        * float(
            train_ratio
        )
    )

    split_index = max(
        1,
        min(
            total - 1,
            split_index,
        ),
    )

    return (
        ordered_rows[
            :split_index
        ],
        ordered_rows[
            split_index:
        ],
    )


__all__ = [
    "chronological_split",
]
