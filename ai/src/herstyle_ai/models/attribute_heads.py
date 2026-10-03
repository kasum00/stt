import torch.nn as nn

from herstyle_ai.training.label_schema import (
    NUM_CLASSES,
)


class AttributeHeads(
    nn.Module
):

    def __init__(
        self,
        hidden_size=384,
        dropout=0.2,
    ):

        super().__init__()

        self.dropout = nn.Dropout(
            dropout
        )

        self.heads = nn.ModuleDict({

            head:
                nn.Linear(
                    hidden_size,
                    num_classes,
                )

            for head, num_classes
            in NUM_CLASSES.items()
        })

    def forward(
        self,
        features,
    ):

        features = self.dropout(
            features
        )

        return {

            head:
                classifier(
                    features
                )

            for head, classifier
            in self.heads.items()
        }