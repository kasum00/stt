from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

from PIL import Image

from transformers import (
    AutoImageProcessor,
    AutoModel,
)


from herstyle_ai.features.color_descriptor import (
    extract_color_descriptor,
)

from herstyle_ai.training.label_schema import (
    ID2LABEL,
    NUM_CLASSES,
)


# =========================================================
# HEAD
# =========================================================

class LinearHead(
    nn.Module
):

    def __init__(
        self,
        input_dim,
        num_classes,
    ):

        super().__init__()

        self.network = nn.Sequential(
            nn.Dropout(
                0.2
            ),
            nn.Linear(
                input_dim,
                num_classes,
            ),
        )

    def forward(
        self,
        x,
    ):

        return self.network(
            x
        )


# =========================================================
# PREDICTOR
# =========================================================

class AttributePredictor:

    def __init__(
        self,
        project_root,
        device=None,
    ):

        self.project_root = Path(
            project_root
        )

        if device is None:

            device = (
                "cuda"
                if torch.cuda.is_available()
                else "cpu"
            )

        self.device = torch.device(
            device
        )

        print(
            "AttributePredictor device:",
            self.device
        )

        # =====================================
        # DINOv2
        # =====================================

        self.model_name = (
            "facebook/dinov2-small"
        )

        self.processor = (
            AutoImageProcessor
            .from_pretrained(
                self.model_name
            )
        )

        self.backbone = (
            AutoModel
            .from_pretrained(
                self.model_name
            )
            .to(
                self.device
            )
        )

        self.backbone.eval()

        for parameter in (
            self.backbone.parameters()
        ):
            parameter.requires_grad = False

        # =====================================
        # Category
        # combined = 768
        # =====================================

        self.category_head = (
            self._load_head(
                head="category",
                input_dim=768,
                checkpoint=(
                    self.project_root
                    / "outputs"
                    / "dinov2_v3"
                    / "checkpoints"
                    / "category__combined__unweighted.pt"
                ),
            )
        )

        # =====================================
        # Material
        # CLS = 384
        # =====================================

        self.material_head = (
            self._load_head(
                head="material",
                input_dim=384,
                checkpoint=(
                    self.project_root
                    / "outputs"
                    / "dinov2_v2"
                    / "best_material.pt"
                ),
            )
        )

        # =====================================
        # Pattern
        # Mean patch = 384
        # =====================================

        self.pattern_head = (
            self._load_head(
                head="pattern",
                input_dim=384,
                checkpoint=(
                    self.project_root
                    / "outputs"
                    / "dinov2_v3"
                    / "checkpoints"
                    / "pattern__mean_patch__weighted.pt"
                ),
            )
        )

        # =====================================
        # Color
        # RGB/HSV = 70
        # =====================================

        color_checkpoint_path = (
            self.project_root
            / "outputs"
            / "color_v4"
            / "checkpoints"
            / "color_descriptor__weighted.pt"
        )

        color_checkpoint = torch.load(
            color_checkpoint_path,
            map_location="cpu",
            weights_only=False,
        )

        self.color_head = LinearHead(
            input_dim=70,
            num_classes=NUM_CLASSES[
                "color"
            ],
        )

        self.color_head.load_state_dict(
            color_checkpoint[
                "model_state_dict"
            ]
        )

        self.color_head = (
            self.color_head
            .to(
                self.device
            )
        )

        self.color_head.eval()

        self.color_mean = (
            color_checkpoint[
                "color_mean"
            ]
            .float()
        )

        self.color_std = (
            color_checkpoint[
                "color_std"
            ]
            .float()
        )

    # =========================================
    # LOAD GENERIC HEAD
    # =========================================

    def _load_head(
        self,
        head,
        input_dim,
        checkpoint,
    ):

        model = LinearHead(
            input_dim=input_dim,
            num_classes=NUM_CLASSES[
                head
            ],
        )

        data = torch.load(
            checkpoint,
            map_location="cpu",
            weights_only=False,
        )

        model.load_state_dict(
            data[
                "model_state_dict"
            ]
        )

        model = model.to(
            self.device
        )

        model.eval()

        return model

    # =========================================
    # TOP-1
    # =========================================

    def _decode(
        self,
        head,
        logits,
    ):

        probabilities = (
            torch.softmax(
                logits,
                dim=1,
            )
        )

        confidence, prediction = (
            probabilities.max(
                dim=1
            )
        )

        prediction_id = int(
            prediction.item()
        )

        return {

            "label":
                ID2LABEL[
                    head
                ][
                    prediction_id
                ],

            "confidence":
                float(
                    confidence.item()
                ),
        }

    # =========================================
    # DINO FEATURES
    # =========================================

    @torch.no_grad()
    def _extract_dinov2(
        self,
        image,
    ):

        processed = self.processor(
            images=image,
            return_tensors="pt",
        )

        pixel_values = (
            processed[
                "pixel_values"
            ]
            .to(
                self.device
            )
        )

        outputs = self.backbone(
            pixel_values=pixel_values
        )

        tokens = (
            outputs
            .last_hidden_state
        )

        cls = tokens[
            :,
            0,
            :
        ]

        mean_patch = (
            tokens[
                :,
                1:,
                :
            ]
            .mean(
                dim=1
            )
        )

        combined = torch.cat(
            [
                cls,
                mean_patch,
            ],
            dim=1,
        )

        return (
            cls,
            mean_patch,
            combined,
        )

    # =========================================
    # PREDICT
    # =========================================

    @torch.no_grad()
    def predict(
        self,
        image_path,
    ):

        image_path = Path(
            image_path
        )

        with Image.open(
            image_path
        ) as image:

            image = image.convert(
                "RGB"
            )

            # =================================
            # DINOv2
            # =================================

            cls, mean_patch, combined = (
                self._extract_dinov2(
                    image
                )
            )

            category_logits = (
                self.category_head(
                    combined
                )
            )

            material_logits = (
                self.material_head(
                    cls
                )
            )

            pattern_logits = (
                self.pattern_head(
                    mean_patch
                )
            )

            # =================================
            # COLOR
            # =================================

            color_descriptor = (
                extract_color_descriptor(
                    image
                )
            )

        color_tensor = torch.tensor(
            color_descriptor,
            dtype=torch.float32,
        )

        # Normalize on CPU exactly as training
        color_tensor = (
            color_tensor
            - self.color_mean
        ) / self.color_std

        color_tensor = (
            color_tensor
            .unsqueeze(0)
            .to(
                self.device
            )
        )

        color_logits = (
            self.color_head(
                color_tensor
            )
        )

        return {

            "category":
                self._decode(
                    "category",
                    category_logits,
                ),

            "color":
                self._decode(
                    "color",
                    color_logits,
                ),

            "material":
                self._decode(
                    "material",
                    material_logits,
                ),

            "pattern":
                self._decode(
                    "pattern",
                    pattern_logits,
                ),
        }