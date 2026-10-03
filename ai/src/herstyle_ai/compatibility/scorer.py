from pathlib import Path

import torch
import yaml

from PIL import Image

from transformers import (
    AutoImageProcessor,
    AutoModel,
)


from herstyle_ai.compatibility.model import (
    CompatibilityNetwork,
)


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
# SCORER
# =========================================================

class CompatibilityScorer:

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
            "CompatibilityScorer device:",
            self.device
        )

        # =====================================
        # CONFIG
        # =====================================

        config_path = (
            self.project_root
            / "configs"
            / "compatibility_final.yaml"
        )

        with open(
            config_path,
            "r",
            encoding="utf-8",
        ) as f:

            config = yaml.safe_load(
                f
            )

        self.backbone_name = (
            config[
                "model"
            ][
                "backbone"
            ]
        )

        self.feature_type = (
            config[
                "model"
            ][
                "feature_type"
            ]
        )

        self.threshold = float(
            config[
                "selection"
            ][
                "threshold"
            ]
        )

        checkpoint_path = (
            self.project_root
            / config[
                "model"
            ][
                "checkpoint"
            ]
        )

        # =====================================
        # DINOv2
        # =====================================

        self.processor = (
            AutoImageProcessor
            .from_pretrained(
                self.backbone_name
            )
        )

        self.backbone = (
            AutoModel
            .from_pretrained(
                self.backbone_name
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
        # COMPATIBILITY MODEL
        # =====================================

        checkpoint = torch.load(
            checkpoint_path,
            map_location="cpu",
            weights_only=False,
        )

        self.model = CompatibilityNetwork(
            input_dim=checkpoint[
                "input_dim"
            ],
            hidden_dim=checkpoint[
                "hidden_dim"
            ],
            pair_dim=checkpoint[
                "pair_dim"
            ],
            dropout=checkpoint[
                "dropout"
            ],
        )

        self.model.load_state_dict(
            checkpoint[
                "model_state_dict"
            ]
        )

        self.model = (
            self.model
            .to(
                self.device
            )
        )

        self.model.eval()

        self.feature_dim = int(
            checkpoint[
                "input_dim"
            ]
        )

    # =====================================================
    # EXTRACT CLS
    # =====================================================

    @torch.no_grad()
    def extract_feature(
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

            inputs = self.processor(
                images=image,
                return_tensors="pt",
            )

        pixel_values = (
            inputs[
                "pixel_values"
            ]
            .to(
                self.device
            )
        )

        outputs = self.backbone(
            pixel_values=pixel_values
        )

        cls = (
            outputs
            .last_hidden_state[
                :,
                0,
                :
            ]
        )

        return cls.squeeze(
            0
        )

    # =====================================================
    # BUILD TENSOR
    # =====================================================

    def _build_outfit_tensor(
        self,
        slot_features,
    ):

        features = []

        mask = []

        for slot in SLOTS:

            feature = (
                slot_features.get(
                    slot
                )
            )

            if feature is None:

                features.append(
                    torch.zeros(
                        self.feature_dim,
                        dtype=torch.float32,
                        device=self.device,
                    )
                )

                mask.append(
                    0.0
                )

            else:

                features.append(
                    feature.to(
                        self.device
                    )
                )

                mask.append(
                    1.0
                )

        features = torch.stack(
            features,
            dim=0,
        )

        mask = torch.tensor(
            mask,
            dtype=torch.float32,
            device=self.device,
        )

        # Add batch dimension
        return (
            features.unsqueeze(0),
            mask.unsqueeze(0),
        )

    # =====================================================
    # SCORE FEATURES
    # =====================================================

    @torch.no_grad()
    def score_features(
        self,
        slot_features,
    ):

        features, mask = (
            self._build_outfit_tensor(
                slot_features
            )
        )

        logits = self.model(
            features,
            mask,
        )

        score = torch.sigmoid(
            logits
        )[0].item()

        return {
            "score":
                float(
                    score
                ),

            "threshold":
                self.threshold,

            "compatible":
                bool(
                    score
                    >= self.threshold
                ),

            "slots":
                [
                    slot

                    for slot in SLOTS

                    if slot in slot_features
                ],
        }

    # =====================================================
    # SCORE IMAGES
    # =====================================================

    @torch.no_grad()
    def score_images(
        self,
        slot_images,
    ):

        """
        Example:

        {
            "top": "...shirt.jpg",
            "bottom": "...skirt.jpg",
            "shoes": "...shoes.jpg"
        }
        """

        invalid_slots = (

            set(
                slot_images.keys()
            )
            -
            set(
                SLOTS
            )
        )

        if invalid_slots:

            raise ValueError(
                f"Unknown slots: "
                f"{sorted(invalid_slots)}"
            )

        if len(
            slot_images
        ) < 2:

            raise ValueError(
                "An outfit must contain at least 2 items."
            )

        # -------------------------------------
        # Prevent invalid base structures
        # -------------------------------------

        has_dress = (
            "dress"
            in slot_images
        )

        has_top = (
            "top"
            in slot_images
        )

        has_bottom = (
            "bottom"
            in slot_images
        )

        if (
            has_dress
            and
            (
                has_top
                or
                has_bottom
            )
        ):

            raise ValueError(
                "Do not mix dress with top/bottom "
                "in Compatibility V1."
            )

        slot_features = {}

        for slot, image_path in (
            slot_images.items()
        ):

            slot_features[
                slot
            ] = self.extract_feature(
                image_path
            )

        result = self.score_features(
            slot_features
        )

        result[
            "items"
        ] = {

            slot:
                str(
                    image_path
                )

            for slot, image_path
            in slot_images.items()
        }

        return result