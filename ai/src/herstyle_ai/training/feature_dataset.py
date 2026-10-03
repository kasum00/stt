import torch

from torch.utils.data import Dataset

from herstyle_ai.training.label_schema import (
    HEAD_NAMES,
)


class FeatureDataset(
    Dataset
):

    def __init__(
        self,
        feature_path,
    ):

        data = torch.load(
            feature_path,
            map_location="cpu",
            weights_only=False,
        )

        self.features = (
            data[
                "features"
            ]
            .float()
        )

        self.labels = (
            data[
                "labels"
            ]
        )

        self.ids = (
            data[
                "ids"
            ]
        )

        self.sources = (
            data[
                "sources"
            ]
        )

        assert (
            len(
                self.features
            )
            ==
            len(
                self.ids
            )
        )

    def __len__(
        self
    ):

        return len(
            self.features
        )

    def __getitem__(
        self,
        index
    ):

        labels = {

            head:
                self.labels[
                    head
                ][
                    index
                ]

            for head in HEAD_NAMES
        }

        return {

            "features":
                self.features[
                    index
                ],

            "labels":
                labels,

            "id":
                self.ids[
                    index
                ],

            "source":
                self.sources[
                    index
                ],
        }