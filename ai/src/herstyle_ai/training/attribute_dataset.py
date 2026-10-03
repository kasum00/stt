from pathlib import Path

import pandas as pd
import torch

from PIL import Image
from torch.utils.data import Dataset

from transformers import (
    AutoImageProcessor,
)

from herstyle_ai.training.label_schema import (
    HEAD_NAMES,
    LABEL2ID,
    IGNORE_INDEX,
)


class AttributeDataset(
    Dataset
):

    def __init__(
        self,
        parquet_path,
        project_root,
        model_name,
        v1_only=True,
    ):

        self.project_root = Path(
            project_root
        )

        self.df = pd.read_parquet(
            parquet_path
        )

        if v1_only:

            self.df = self.df[
                self.df[
                    "v1_training_eligible"
                ] == True
            ].copy()

        self.df = self.df.reset_index(
            drop=True
        )

        self.processor = (
            AutoImageProcessor
            .from_pretrained(
                model_name
            )
        )

    def __len__(
        self
    ):

        return len(
            self.df
        )

    def encode_label(
        self,
        head,
        value,
    ):

        if value is None:

            return IGNORE_INDEX

        try:

            if pd.isna(value):

                return IGNORE_INDEX

        except (
            TypeError,
            ValueError,
        ):
            pass

        mapping = LABEL2ID[
            head
        ]

        if value not in mapping:

            raise ValueError(
                f"Unknown {head} label: {value}"
            )

        return mapping[
            value
        ]

    def __getitem__(
        self,
        index
    ):

        row = self.df.iloc[
            index
        ]

        image_path = (
            self.project_root
            / str(
                row[
                    "image"
                ]
            )
        )

        with Image.open(
            image_path
        ) as image:

            image = image.convert(
                "RGB"
            )

            processed = (
                self.processor(
                    images=image,
                    return_tensors="pt",
                )
            )

        pixel_values = (
            processed[
                "pixel_values"
            ][0]
        )

        labels = {

            head:
                torch.tensor(
                    self.encode_label(
                        head,
                        row.get(
                            head
                        ),
                    ),
                    dtype=torch.long,
                )

            for head in HEAD_NAMES
        }

        return {

            "id":
                row[
                    "id"
                ],

            "source":
                row[
                    "source"
                ],

            "pixel_values":
                pixel_values,

            "labels":
                labels,
        }