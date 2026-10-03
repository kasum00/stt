from pathlib import Path

import torch
import torch.nn as nn

from PIL import Image

from transformers import (
    AutoImageProcessor,
    AutoModel,
)


from herstyle_ai.vlm.qwen_vlm_predictor import (
    QwenFashionVLM,
)

from herstyle_ai.features.color_descriptor import (
    extract_color_descriptor,
)

from herstyle_ai.training.label_schema import (
    ID2LABEL,
    NUM_CLASSES,
)


# =========================================================
# LINEAR HEAD
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
            nn.Dropout(0.2),
            nn.Linear(
                input_dim,
                num_classes,
            ),
        )

    def forward(
        self,
        x,
    ):

        return self.network(x)


# =========================================================
# HYBRID PREDICTOR
# =========================================================

class HybridAttributePredictor:

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
            "Hybrid device:",
            self.device
        )

        # =====================================
        # VLM
        # =====================================

        self.vlm = QwenFashionVLM(
            project_root=self.project_root
        )

        # =====================================
        # DINOv2
        # =====================================

        self.dino_name = (
            "facebook/dinov2-small"
        )

        self.dino_processor = (
            AutoImageProcessor
            .from_pretrained(
                self.dino_name
            )
        )

        self.dino = (
            AutoModel
            .from_pretrained(
                self.dino_name
            )
            .to(
                self.device
            )
        )

        self.dino.eval()

        for parameter in (
            self.dino.parameters()
        ):

            parameter.requires_grad = False

        # =====================================
        # CATEGORY FALLBACK
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
        # MATERIAL MAIN
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
        # PATTERN FALLBACK
        # MeanPatch = 384
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
        # COLOR FALLBACK
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
            ].float()
        )

        self.color_std = (
            color_checkpoint[
                "color_std"
            ].float()
        )

    # =====================================================
    # LOAD HEAD
    # =====================================================

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

    # =====================================================
    # DECODE
    # =====================================================

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

    def _decode_topk(
        self,
        head,
        logits,
        k=3,
    ):

        probabilities = torch.softmax(
            logits,
            dim=1,
        )

        k = min(
            k,
            probabilities.shape[1],
        )

        values, indices = torch.topk(
            probabilities,
            k=k,
            dim=1,
        )

        result = []

        for score, index in zip(
            values[0],
            indices[0],
        ):

            index = int(
                index.item()
            )

            result.append(
                {
                    "label":
                        ID2LABEL[
                            head
                        ][
                            index
                        ],

                    "score":
                        float(
                            score.item()
                        ),
                }
            )

        return result

    # =====================================================
    # DINO FEATURES
    # =====================================================

    @torch.no_grad()
    def _extract_dino_features(
        self,
        image,
    ):

        processed = (
            self.dino_processor(
                images=image,
                return_tensors="pt",
            )
        )

        pixel_values = (
            processed[
                "pixel_values"
            ]
            .to(
                self.device
            )
        )

        output = self.dino(
            pixel_values=pixel_values
        )

        tokens = (
            output.last_hidden_state
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

    # =====================================================
    # COLOR FALLBACK
    # =====================================================

    @torch.no_grad()
    def _predict_color_fallback(
        self,
        image,
    ):

        descriptor = (
            extract_color_descriptor(
                image
            )
        )

        feature = torch.tensor(
            descriptor,
            dtype=torch.float32,
        )

        # Normalize CPU
        feature = (
            feature
            - self.color_mean
        ) / self.color_std

        feature = (
            feature
            .unsqueeze(0)
            .to(
                self.device
            )
        )

        logits = self.color_head(
            feature
        )

        return self._decode(
            "color",
            logits,
        )

    # =====================================================
    # PREDICT
    # =====================================================

    @torch.no_grad()
    def predict(
        self,
        image_path,
    ):

        image_path = Path(
            image_path
        )

        # =====================================
        # VLM
        # =====================================

        vlm_result = (
            self.vlm.predict(
                image_path
            )
        )

        vlm_prediction = (
            vlm_result[
                "prediction"
            ]
        )

        # =====================================
        # IMAGE
        # =====================================

        with Image.open(
            image_path
        ) as image:

            image = image.convert(
                "RGB"
            )

            # =================================
            # DINO
            # =================================

            (
                cls,
                mean_patch,
                combined,
            ) = self._extract_dino_features(
                image
            )

            # =================================
            # MATERIAL - SPECIALIZED MAIN
            # =================================

            material_logits = (
                self.material_head(
                    cls
                )
            )

            material_candidates = (
                self._decode_topk(
                    "material",
                    material_logits,
                    k=3,
                )
            )

            # =================================
            # CATEGORY
            # =================================

            category = (
                vlm_prediction.get(
                    "category"
                )
            )

            category_source = "vlm"

            category_confidence = None

            if category is None:

                logits = (
                    self.category_head(
                        combined
                    )
                )

                fallback = (
                    self._decode(
                        "category",
                        logits,
                    )
                )

                category = (
                    fallback[
                        "label"
                    ]
                )

                category_confidence = (
                    fallback[
                        "confidence"
                    ]
                )

                category_source = (
                    "dinov2_fallback"
                )

            # =================================
            # PATTERN
            # =================================

            pattern = (
                vlm_prediction.get(
                    "pattern"
                )
            )

            pattern_source = "vlm"

            pattern_confidence = None

            if pattern is None:

                logits = (
                    self.pattern_head(
                        mean_patch
                    )
                )

                fallback = (
                    self._decode(
                        "pattern",
                        logits,
                    )
                )

                pattern = (
                    fallback[
                        "label"
                    ]
                )

                pattern_confidence = (
                    fallback[
                        "confidence"
                    ]
                )

                pattern_source = (
                    "dinov2_fallback"
                )

            # =================================
            # COLOR
            # =================================

            color = (
                vlm_prediction.get(
                    "color"
                )
            )

            color_source = "vlm"

            color_confidence = None

            if color is None:

                fallback = (
                    self._predict_color_fallback(
                        image
                    )
                )

                color = (
                    fallback[
                        "label"
                    ]
                )

                color_confidence = (
                    fallback[
                        "confidence"
                    ]
                )

                color_source = (
                    "rgb_hsv_fallback"
                )

        # =====================================
        # OUTPUT
        # =====================================

        return {

            "category": {
                "label":
                    category,

                "source":
                    category_source,

                "confidence":
                    category_confidence,
            },

            "subcategory": {
                "label":
                    vlm_prediction.get(
                        "subcategory"
                    ),

                "source":
                    "vlm",
            },

            "color": {
                "label":
                    color,

                "source":
                    color_source,

                "confidence":
                    color_confidence,
            },

            "material": {

                "label":
                    None,

                "source":
                    "dinov2_suggestion",

                "status":
                    "needs_confirmation",

                "candidates":
                    material_candidates,
            },

            "pattern": {
                "label":
                    pattern,

                "source":
                    pattern_source,

                "confidence":
                    pattern_confidence,
            },

            "sleeve_length": {
                "label":
                    vlm_prediction.get(
                        "sleeve_length"
                    ),

                "source":
                    "vlm",
            },

            "neckline": {
                "label":
                    vlm_prediction.get(
                        "neckline"
                    ),

                "source":
                    "vlm",
            },

            "fit": {
                "label":
                    vlm_prediction.get(
                        "fit"
                    ),

                "source":
                    "vlm",
            },

            "design_details": {
                "labels":
                    vlm_prediction.get(
                        "design_details",
                        [],
                    ),

                "source":
                    "vlm",
            },

            "_debug": {

                "vlm_rejected":
                    vlm_result.get(
                        "rejected",
                        {}
                    ),
            },
        }