import torch


def calculate_class_weights(
    labels,
    num_classes,
    max_weight=3.0,
):

    counts = torch.bincount(
        labels,
        minlength=num_classes,
    ).float()

    weights = torch.zeros(
        num_classes,
        dtype=torch.float32,
    )

    valid = counts > 0

    weights[
        valid
    ] = (
        1.0
        /
        torch.sqrt(
            counts[
                valid
            ]
        )
    )

    if valid.any():

        mean_weight = (
            weights[
                valid
            ].mean()
        )

        weights[
            valid
        ] = (
            weights[
                valid
            ]
            / mean_weight
        )

    weights = torch.clamp(
        weights,
        max=max_weight,
    )

    return (
        weights,
        counts,
    )