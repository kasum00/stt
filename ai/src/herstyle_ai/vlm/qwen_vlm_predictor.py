import json
import re
from importlib.util import find_spec

import torch
import yaml

from pathlib import Path
from PIL import Image

from transformers import (
    AutoProcessor,
    AutoModelForMultimodalLM,
)

from herstyle_ai.vlm.fashion_prompt import (
    build_fashion_prompt,
)

from herstyle_ai.vlm.taxonomy_validator import (
    validate_prediction,
)


MAX_VLM_IMAGE_SIDE = 1024


class QwenFashionVLM:

    def __init__(
        self,
        project_root,
    ):

        self.project_root = Path(
            project_root
        )

        config_path = (
            self.project_root
            / "configs"
            / "vlm.yaml"
        )

        with open(
            config_path,
            "r",
            encoding="utf-8",
        ) as f:

            config = yaml.safe_load(
                f
            )

        self.model_name = (
            config[
                "model"
            ][
                "name"
            ]
        )

        self.max_new_tokens = int(
            config[
                "model"
            ].get(
                "max_new_tokens",
                512,
            )
        )

        print(
            "Loading VLM:",
            self.model_name
        )

        self.processor = (
            AutoProcessor
            .from_pretrained(
                self.model_name
            )
        )

        # `device_map="auto"` is the preferred loading path for the
        # multimodal model, but Transformers requires the optional
        # `accelerate` package for that path.  Keep local development
        # usable when the environment was installed without the optional
        # package: load normally, then move the model to the available
        # device explicitly.
        has_accelerate = find_spec("accelerate") is not None
        model_kwargs = {
            "torch_dtype": "auto",
        }

        if has_accelerate:
            model_kwargs["device_map"] = "auto"

        self.model = (
            AutoModelForMultimodalLM
            .from_pretrained(
                self.model_name,
                **model_kwargs,
            )
        )

        if not has_accelerate:
            device = (
                "cuda"
                if torch.cuda.is_available()
                else "cpu"
            )
            self.model = self.model.to(device)

        self.model.eval()

    # =========================================
    # JSON EXTRACTION
    # =========================================

    def extract_json(
        self,
        text,
    ):

        text = text.strip()

        # Remove optional markdown fence
        text = re.sub(
            r"^```(?:json)?",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"```$",
            "",
            text,
        )

        text = text.strip()

        start = text.find(
            "{"
        )

        end = text.rfind(
            "}"
        )

        if (
            start == -1
            or end == -1
            or end <= start
        ):

            raise ValueError(
                "VLM output does not contain JSON:\n"
                + text
            )

        json_text = text[
            start:
            end + 1
        ]

        return json.loads(
            json_text
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

        with Image.open(image_path) as source_image:
            image = source_image.convert("RGB")

        # Large phone photos can create an unnecessarily large number of
        # visual tokens for Qwen-VL.  Keep the original upload untouched,
        # but cap only the temporary image used by the VLM so recognition
        # remains responsive for high-resolution and batch uploads.
        image.thumbnail(
            (MAX_VLM_IMAGE_SIDE, MAX_VLM_IMAGE_SIDE),
            Image.Resampling.LANCZOS,
        )

        prompt = (
            build_fashion_prompt()
        )

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": image,
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        ]

        inputs = (
            self.processor
            .apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt",
            )
        )

        inputs = inputs.to(
            self.model.device
        )

        generated_ids = (
            self.model.generate(
                **inputs,
                max_new_tokens=(
                    self.max_new_tokens
                ),
                do_sample=False,
            )
        )

        generated_ids = (
            generated_ids[
                :,
                inputs[
                    "input_ids"
                ].shape[
                    1
                ]:
            ]
        )

        text = (
            self.processor
            .batch_decode(
                generated_ids,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )[0]
        )

        result = (
            self.extract_json(
                text
            )
        )

        validated = (
            validate_prediction(
                result
            )
        )

        return {

            "raw_text":
                text,

            "raw_prediction":
                result,

            "prediction":
                validated[
                    "prediction"
                ],

            "rejected":
                validated[
                    "rejected"
                ],
        }
