import torch
import torch.nn as nn


# =========================================================
# CONFIG
# =========================================================

NUM_SLOTS = 5


# =========================================================
# COMPATIBILITY NETWORK
# =========================================================

class CompatibilityNetwork(
    nn.Module
):

    def __init__(
        self,
        input_dim=768,
        hidden_dim=256,
        pair_dim=256,
        dropout=0.2,
    ):

        super().__init__()

        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.pair_dim = pair_dim

        # =====================================
        # SHARED ITEM PROJECTION
        #
        # DINO embedding:
        # 768 -> 256
        # =====================================

        self.item_projection = nn.Sequential(

            nn.Linear(
                input_dim,
                hidden_dim,
            ),

            nn.LayerNorm(
                hidden_dim
            ),

            nn.GELU(),

            nn.Dropout(
                dropout
            ),
        )

        # =====================================
        # LEARNED SLOT EMBEDDINGS
        #
        # slot 0 = top
        # slot 1 = bottom
        # slot 2 = dress
        # slot 3 = outerwear
        # slot 4 = shoes
        # =====================================

        self.slot_embeddings = nn.Parameter(

            torch.randn(
                NUM_SLOTS,
                hidden_dim,
            ) * 0.02

        )

        # =====================================
        # PAIR NETWORK
        #
        # For pair (i, j):
        #
        # zi
        # zj
        # |zi - zj|
        # zi * zj
        #
        # total = hidden_dim * 4
        # =====================================

        self.pair_network = nn.Sequential(

            nn.Linear(
                hidden_dim * 4,
                pair_dim,
            ),

            nn.LayerNorm(
                pair_dim
            ),

            nn.GELU(),

            nn.Dropout(
                dropout
            ),

            nn.Linear(
                pair_dim,
                pair_dim,
            ),

            nn.GELU(),
        )

        # =====================================
        # FINAL OUTFIT SCORER
        #
        # global pooled representation
        # +
        # pairwise pooled representation
        # +
        # slot presence mask
        # =====================================

        final_dim = (
            hidden_dim
            +
            pair_dim
            +
            NUM_SLOTS
        )

        self.scorer = nn.Sequential(

            nn.Linear(
                final_dim,
                256,
            ),

            nn.GELU(),

            nn.Dropout(
                dropout
            ),

            nn.Linear(
                256,
                64,
            ),

            nn.GELU(),

            nn.Dropout(
                dropout
            ),

            nn.Linear(
                64,
                1,
            ),
        )

    # =====================================================
    # FORWARD
    # =====================================================

    def forward(
        self,
        features,
        mask,
    ):

        """
        features:
            [B, 5, input_dim]

        mask:
            [B, 5]

        returns:
            logits [B]
        """

        batch_size = (
            features.shape[
                0
            ]
        )

        # =====================================
        # ITEM PROJECTION
        # =====================================

        z = self.item_projection(
            features
        )

        # z:
        # [B, 5, hidden_dim]

        # =====================================
        # ADD SLOT EMBEDDING
        # =====================================

        slot_embedding = (
            self.slot_embeddings
            .unsqueeze(0)
        )

        # [1, 5, hidden_dim]

        z = (
            z
            +
            slot_embedding
        )

        # Zero absent slots again
        expanded_mask = (
            mask
            .unsqueeze(-1)
        )

        z = (
            z
            *
            expanded_mask
        )

        # =====================================
        # GLOBAL OUTFIT REPRESENTATION
        #
        # masked mean of available items
        # =====================================

        slot_count = (
            mask.sum(
                dim=1,
                keepdim=True,
            )
            .clamp(
                min=1.0
            )
        )

        global_representation = (

            z.sum(
                dim=1
            )

            /

            slot_count
        )

        # [B, hidden_dim]

        # =====================================
        # PAIRWISE INTERACTIONS
        # =====================================

        pair_representations = []

        pair_masks = []

        for i in range(
            NUM_SLOTS
        ):

            for j in range(
                i + 1,
                NUM_SLOTS,
            ):

                zi = z[
                    :,
                    i,
                    :
                ]

                zj = z[
                    :,
                    j,
                    :
                ]

                # Pair only exists when
                # both slots exist.
                pair_mask = (
                    mask[
                        :,
                        i
                    ]
                    *
                    mask[
                        :,
                        j
                    ]
                )

                pair_input = torch.cat(
                    [
                        zi,
                        zj,
                        torch.abs(
                            zi - zj
                        ),
                        zi * zj,
                    ],
                    dim=1,
                )

                pair_representation = (
                    self.pair_network(
                        pair_input
                    )
                )

                pair_representation = (
                    pair_representation
                    *
                    pair_mask.unsqueeze(
                        1
                    )
                )

                pair_representations.append(
                    pair_representation
                )

                pair_masks.append(
                    pair_mask
                )

        # =====================================
        # STACK PAIRS
        # =====================================

        pair_representations = (
            torch.stack(
                pair_representations,
                dim=1,
            )
        )

        # [B, 10, pair_dim]

        pair_masks = torch.stack(
            pair_masks,
            dim=1,
        )

        # [B, 10]

        # =====================================
        # MASKED PAIR MEAN
        # =====================================

        pair_count = (
            pair_masks
            .sum(
                dim=1,
                keepdim=True,
            )
            .clamp(
                min=1.0
            )
        )

        pair_representation = (

            pair_representations
            .sum(
                dim=1
            )

            /

            pair_count
        )

        # [B, pair_dim]

        # =====================================
        # FINAL REPRESENTATION
        # =====================================

        outfit_representation = (
            torch.cat(
                [
                    global_representation,
                    pair_representation,
                    mask,
                ],
                dim=1,
            )
        )

        # =====================================
        # SCORE
        # =====================================

        logits = self.scorer(
            outfit_representation
        )

        # [B, 1]
        logits = logits.squeeze(
            1
        )

        return logits