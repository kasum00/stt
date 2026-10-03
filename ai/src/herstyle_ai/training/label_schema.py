from pathlib import Path

import yaml


PROJECT_ROOT = (
    Path(__file__).resolve().parents[3]
)

CONFIG_PATH = (
    PROJECT_ROOT
    / "configs"
    / "dinov2_v1.yaml"
)


def load_config():

    with open(
        CONFIG_PATH,
        "r",
        encoding="utf-8",
    ) as f:

        return yaml.safe_load(f)


CONFIG = load_config()

HEAD_NAMES = [
    "category",
    "color",
    "material",
    "pattern",
]


LABELS = {

    head:
        CONFIG[
            "heads"
        ][
            head
        ][
            "labels"
        ]

    for head in HEAD_NAMES
}


LABEL2ID = {

    head: {
        label: index
        for index, label
        in enumerate(
            LABELS[
                head
            ]
        )
    }

    for head in HEAD_NAMES
}


ID2LABEL = {

    head: {
        index: label
        for index, label
        in enumerate(
            LABELS[
                head
            ]
        )
    }

    for head in HEAD_NAMES
}


NUM_CLASSES = {

    head:
        len(
            LABELS[
                head
            ]
        )

    for head in HEAD_NAMES
}


IGNORE_INDEX = -100