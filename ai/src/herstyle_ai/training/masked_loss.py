import torch
import torch.nn as nn

from herstyle_ai.training.label_schema import (
    HEAD_NAMES,
    IGNORE_INDEX,
)


class MaskedMultiHeadLoss(
    nn.Module
):

    def __init__(
        self,
        head_weights=None,
    ):

        super().__init__()

        if head_weights is None:

            head_weights = {
                head: 1.0
                for head in HEAD_NAMES
            }

        self.head_weights = (
            head_weights
        )

        self.criterion = (
            nn.CrossEntropyLoss()
        )

    def forward(
        self,
        logits,
        labels,
    ):

        total_loss = None

        head_losses = {}

        valid_counts = {}

        active_heads = 0

        for head in HEAD_NAMES:

            head_logits = (
                logits[
                    head
                ]
            )

            head_labels = (
                labels[
                    head
                ]
            )

            # =================================
            # Only annotated samples
            # =================================

            valid_mask = (
                head_labels
                != IGNORE_INDEX
            )

            valid_count = int(
                valid_mask.sum().item()
            )

            valid_counts[
                head
            ] = valid_count

            # =================================
            # Entire batch has no labels
            # for this head
            # =================================

            if valid_count == 0:

                head_losses[
                    head
                ] = None

                continue

            valid_logits = (
                head_logits[
                    valid_mask
                ]
            )

            valid_labels = (
                head_labels[
                    valid_mask
                ]
            )

            loss = self.criterion(
                valid_logits,
                valid_labels,
            )

            weighted_loss = (
                loss
                * self.head_weights[
                    head
                ]
            )

            if total_loss is None:

                total_loss = (
                    weighted_loss
                )

            else:

                total_loss = (
                    total_loss
                    + weighted_loss
                )

            head_losses[
                head
            ] = loss

            active_heads += 1

        # =====================================
        # Safety
        # =====================================

        if total_loss is None:

            raise RuntimeError(
                "Batch contains no valid labels "
                "for any prediction head."
            )

        # Normalize by number of active heads
        total_loss = (
            total_loss
            / active_heads
        )

        return {

            "loss":
                total_loss,

            "head_losses":
                head_losses,

            "valid_counts":
                valid_counts,

            "active_heads":
                active_heads,
        }