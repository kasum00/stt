import torch

from torch.utils.data import Dataset

from herstyle_ai.training.label_schema import (
    IGNORE_INDEX,
)


class SingleHeadFeatureDataset(
    Dataset
):

    def __init__(
        self,
        feature_path,
        head,
    ):

        data = torch.load(
            feature_path,
            map_location="cpu",
            weights_only=False,
        )

        features = (
            data[
                "features"
            ]
            .float()
        )

        labels = (
            data[
                "labels"
            ][
                head
            ]
            .long()
        )

        valid_mask = (
            labels
            != IGNORE_INDEX
        )

        self.features = (
            features[
                valid_mask
            ]
        )

        self.labels = (
            labels[
                valid_mask
            ]
        )

    def __len__(
        self,
    ):

        return len(
            self.features
        )

    def __getitem__(
        self,
        index,
    ):

        return (
            self.features[
                index
            ],
            self.labels[
                index
            ],
        )