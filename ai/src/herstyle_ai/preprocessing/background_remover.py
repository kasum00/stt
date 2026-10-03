from pathlib import Path
from uuid import uuid4
from io import BytesIO

from PIL import Image

from rembg import (
    new_session,
    remove,
)


class BackgroundRemover:

    def __init__(
        self,
        project_root: Path,
        data_root=None,
        model_name="isnet-general-use",
    ):

        self.project_root = Path(
            project_root
        )
        self.data_root = Path(data_root) if data_root is not None else self.project_root / "data"

        self.model_name = (
            model_name
        )

        # =====================================
        # OUTPUT DIRECTORY
        # =====================================

        self.output_dir = (
            self.data_root
            / "processed"
            / "wardrobe_images"
        )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        # =====================================
        # LOAD REMBG MODEL ONCE
        # =====================================

        print(
            "Loading background removal model:",
            self.model_name,
        )

        self.session = new_session(
            self.model_name
        )

    # =====================================================
    # WHITE BACKGROUND
    # =====================================================

    @staticmethod
    def _composite_on_white(
        image: Image.Image,
    ) -> Image.Image:

        image = image.convert(
            "RGBA"
        )

        background = Image.new(
            "RGBA",
            image.size,
            (
                255,
                255,
                255,
                255,
            ),
        )

        composed = Image.alpha_composite(
            background,
            image,
        )

        return composed.convert(
            "RGB"
        )

    # =====================================================
    # PROCESS
    # =====================================================

    def process(
        self,
        image_path,
        output_id=None,
    ):

        image_path = Path(
            image_path
        )

        if not image_path.is_file():

            raise FileNotFoundError(
                f"Image not found: {image_path}"
            )

        if output_id is None:

            output_id = (
                uuid4().hex
            )

        # =====================================
        # READ ORIGINAL
        # =====================================

        with open(
            image_path,
            "rb",
        ) as f:

            input_bytes = (
                f.read()
            )

        # =====================================
        # REMOVE BACKGROUND
        # =====================================

        output_bytes = remove(
            input_bytes,
            session=self.session,
        )

        transparent_image = (
            Image.open(
                BytesIO(
                    output_bytes
                )
            )
            .convert(
                "RGBA"
            )
        )

        # =====================================
        # PATHS
        # =====================================

        transparent_path = (
            self.output_dir
            / f"{output_id}_transparent.png"
        )

        model_input_path = (
            self.output_dir
            / f"{output_id}_model.png"
        )

        # =====================================
        # SAVE TRANSPARENT
        # =====================================

        transparent_image.save(
            transparent_path,
            format="PNG",
        )

        # =====================================
        # CREATE MODEL INPUT
        #
        # Explicit white background.
        # =====================================

        model_image = (
            self._composite_on_white(
                transparent_image
            )
        )

        model_image.save(
            model_input_path,
            format="PNG",
        )

        return {

            "original_image_path":
                str(
                    image_path.resolve()
                ),

            "transparent_image_path":
                str(
                    transparent_path.resolve()
                ),

            "model_input_path":
                str(
                    model_input_path.resolve()
                ),

            "background_model":
                self.model_name,
        }
