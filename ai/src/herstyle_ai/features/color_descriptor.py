import numpy as np

from PIL import Image


def normalized_histogram(
    values,
    bins,
):

    histogram, _ = np.histogram(
        values,
        bins=bins,
        range=(0, 256),
    )

    histogram = histogram.astype(
        np.float32
    )

    total = histogram.sum()

    if total > 0:
        histogram /= total

    return histogram


def extract_color_descriptor(
    image,
):

    if not isinstance(
        image,
        Image.Image,
    ):
        image = Image.open(
            image
        )

    image = image.convert(
        "RGB"
    )

    width, height = (
        image.size
    )

    # Same crop as V4 training
    crop_width = int(
        width * 0.70
    )

    crop_height = int(
        height * 0.80
    )

    left = (
        width - crop_width
    ) // 2

    top = (
        height - crop_height
    ) // 2

    image = image.crop(
        (
            left,
            top,
            left + crop_width,
            top + crop_height,
        )
    )

    image = image.resize(
        (
            128,
            128,
        )
    )

    # =========================================
    # RGB
    # =========================================

    rgb = np.asarray(
        image,
        dtype=np.float32,
    )

    rgb_flat = rgb.reshape(
        -1,
        3,
    )

    rgb_mean = (
        rgb_flat.mean(
            axis=0
        )
        / 255.0
    )

    rgb_std = (
        rgb_flat.std(
            axis=0
        )
        / 255.0
    )

    rgb_hist = []

    for channel in range(3):

        rgb_hist.extend(
            normalized_histogram(
                rgb_flat[:, channel],
                bins=8,
            )
        )

    # =========================================
    # HSV
    # =========================================

    hsv = np.asarray(
        image.convert(
            "HSV"
        ),
        dtype=np.float32,
    )

    hsv_flat = hsv.reshape(
        -1,
        3,
    )

    hsv_mean = (
        hsv_flat.mean(
            axis=0
        )
        / 255.0
    )

    hsv_std = (
        hsv_flat.std(
            axis=0
        )
        / 255.0
    )

    h_hist = normalized_histogram(
        hsv_flat[:, 0],
        bins=18,
    )

    s_hist = normalized_histogram(
        hsv_flat[:, 1],
        bins=8,
    )

    v_hist = normalized_histogram(
        hsv_flat[:, 2],
        bins=8,
    )

    descriptor = np.concatenate(
        [
            rgb_mean,
            rgb_std,
            np.asarray(
                rgb_hist,
                dtype=np.float32,
            ),
            hsv_mean,
            hsv_std,
            h_hist,
            s_hist,
            v_hist,
        ]
    )

    return descriptor.astype(
        np.float32
    )