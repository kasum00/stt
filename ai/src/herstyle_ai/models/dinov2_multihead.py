import torch
import torch.nn as nn

from transformers import AutoModel

from herstyle_ai.training.label_schema import (
    NUM_CLASSES,
)


class Dinov2MultiHead(
    nn.Module
):

    def __init__(
        self,
        model_name,
        freeze_backbone=True,
        dropout=0.2,
    ):

        super().__init__()

        # =====================================
        # Backbone
        # =====================================

        self.backbone = (
            AutoModel.from_pretrained(
                model_name
            )
        )

        self.hidden_size = (
            self.backbone.config.hidden_size
        )

        self.freeze_backbone = (
            freeze_backbone
        )

        if self.freeze_backbone:

            for parameter in (
                self.backbone.parameters()
            ):

                parameter.requires_grad = False

        # =====================================
        # Shared dropout
        # =====================================

        self.dropout = nn.Dropout(
            dropout
        )

        # =====================================
        # Heads
        # =====================================

        self.heads = (
            nn.ModuleDict({

                head:
                    nn.Linear(
                        self.hidden_size,
                        num_classes,
                    )

                for head, num_classes
                in NUM_CLASSES.items()
            })
        )

    # =========================================
    # Preserve frozen backbone in eval mode
    # =========================================

    def train(
        self,
        mode=True,
    ):

        super().train(
            mode
        )

        if self.freeze_backbone:

            self.backbone.eval()

        return self

    # =========================================
    # Forward
    # =========================================

    def forward(
        self,
        pixel_values,
    ):

        # Frozen backbone does not need
        # gradient graph.
        if self.freeze_backbone:

            with torch.no_grad():

                outputs = self.backbone(
                    pixel_values=pixel_values
                )

        else:

            outputs = self.backbone(
                pixel_values=pixel_values
            )

        # DINOv2:
        # token index 0 = CLS token
        #
        # shape:
        # [batch, hidden_size]
        cls_embedding = (
            outputs
            .last_hidden_state[
                :,
                0,
                :
            ]
        )

        features = self.dropout(
            cls_embedding
        )

        logits = {

            head:
                classifier(
                    features
                )

            for head, classifier
            in self.heads.items()
        }

        return {

            "features":
                features,

            "logits":
                logits,
        }