from pathlib import Path

import pandas as pd
import torch

from torch.utils.data import Dataset


# =========================================================
# SLOT CONFIG
# =========================================================

SLOTS = [
    "top",
    "bottom",
    "dress",
    "outerwear",
    "shoes",
]


# =========================================================
# DATASET
# =========================================================

class CompatibilityDataset(
    Dataset
):

    def __init__(
        self,
        parquet_path,
        feature_path,
        feature_type="combined",
    ):

        self.parquet_path = Path(
            parquet_path
        )

        self.feature_path = Path(
            feature_path
        )

        self.feature_type = (
            feature_type
        )

        # =====================================
        # LOAD EXAMPLES
        # =====================================

        self.df = pd.read_parquet(
            self.parquet_path
        )

        self.df = self.df.reset_index(
            drop=True
        )

        # =====================================
        # LOAD CACHED FEATURES
        # =====================================

        feature_data = torch.load(
            self.feature_path,
            map_location="cpu",
            weights_only=False,
        )

        if (
            self.feature_type
            not in feature_data
        ):

            raise ValueError(
                f"Unknown feature type: "
                f"{self.feature_type}"
            )

        self.features = (
            feature_data[
                self.feature_type
            ]
            .float()
        )

        self.item_keys = [
            str(x)
            for x in feature_data[
                "item_keys"
            ]
        ]

        # =====================================
        # INDEX
        # =====================================

        self.item_index = {

            item_key:
                index

            for index, item_key
            in enumerate(
                self.item_keys
            )
        }

        self.feature_dim = (
            self.features.shape[
                1
            ]
        )

    # =====================================================
    # LENGTH
    # =====================================================

    def __len__(
        self,
    ):

        return len(
            self.df
        )

    # =====================================================
    # GET FEATURE
    # =====================================================

    def _get_feature(
        self,
        item_key,
    ):

        if (
            item_key is None
            or
            pd.isna(
                item_key
            )
        ):

            return None

        item_key = str(
            item_key
        )

        index = self.item_index.get(
            item_key
        )

        if index is None:

            raise KeyError(
                f"Feature not found for item: "
                f"{item_key}"
            )

        return self.features[
            index
        ]

    # =====================================================
    # GET ITEM
    # =====================================================

    def __getitem__(
        self,
        index,
    ):

        row = self.df.iloc[
            index
        ]

        slot_features = []

        mask = []

        item_keys = []

        for slot in SLOTS:

            item_key = row.get(
                f"{slot}_key"
            )

            feature = (
                self._get_feature(
                    item_key
                )
            )

            if feature is None:

                slot_features.append(
                    torch.zeros(
                        self.feature_dim,
                        dtype=torch.float32,
                    )
                )

                mask.append(
                    0.0
                )

                # Do not use None because
                # PyTorch default_collate cannot batch NoneType.
                item_keys.append(
                    ""
                )
            else:

                slot_features.append(
                    feature
                )

                mask.append(
                    1.0
                )

                item_keys.append(
                    str(
                        item_key
                    )
                )

        # Shape:
        # [5, feature_dim]
        x = torch.stack(
            slot_features,
            dim=0,
        )

        # Shape:
        # [5]
        mask = torch.tensor(
            mask,
            dtype=torch.float32,
        )

        label = torch.tensor(
            float(
                row[
                    "label"
                ]
            ),
            dtype=torch.float32,
        )

        return {

            "features":
                x,

            "mask":
                mask,

            "label":
                label,

            "item_keys":
                item_keys,

            "example_id":
                row[
                    "example_id"
                ],

            "slot_signature":
                row[
                    "slot_signature"
                ],
        }