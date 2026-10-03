from pathlib import Path
import hashlib

from PIL import Image


MIN_WIDTH = 224
MIN_HEIGHT = 224


def calculate_md5(
    path: Path
):

    hasher = hashlib.md5()

    with open(
        path,
        "rb"
    ) as f:

        for chunk in iter(
            lambda: f.read(8192),
            b""
        ):

            hasher.update(
                chunk
            )

    return hasher.hexdigest()


def validate_image(
    path: Path
):

    result = {
        "valid": False,
        "width": None,
        "height": None,
        "mode": None,
        "format": None,
        "md5": None,
        "error": None,
    }

    if not path.exists():

        result[
            "error"
        ] = "file_not_found"

        return result

    try:

        # =====================================
        # Verify file integrity
        # =====================================

        with Image.open(
            path
        ) as image:

            image.verify()

        # =====================================
        # Reopen after verify
        # =====================================

        with Image.open(
            path
        ) as image:

            width, height = (
                image.size
            )

            result[
                "width"
            ] = width

            result[
                "height"
            ] = height

            result[
                "mode"
            ] = image.mode

            result[
                "format"
            ] = image.format

            # =================================
            # Size validation
            # =================================

            if (
                width < MIN_WIDTH
                or
                height < MIN_HEIGHT
            ):

                result[
                    "error"
                ] = "image_too_small"

                return result

            # =================================
            # RGB conversion validation
            # =================================

            image.convert(
                "RGB"
            )

        # =====================================
        # Hash
        # =====================================

        result[
            "md5"
        ] = calculate_md5(
            path
        )

        result[
            "valid"
        ] = True

        return result

    except Exception as exc:

        result[
            "error"
        ] = str(exc)

        return result