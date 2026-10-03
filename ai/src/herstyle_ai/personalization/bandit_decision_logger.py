from pathlib import Path

from herstyle_ai.personalization.bandit_exposure import (
    build_bandit_exposure,
)

from herstyle_ai.personalization.bandit_exposure_repository import (
    BanditExposureRepository,
)


class BanditDecisionLogger:

    def __init__(
        self,
        project_root,
        data_root=None,
    ):

        self.project_root = Path(
            project_root
        )

        self.repository = (
            BanditExposureRepository(
                project_root=self.project_root,
                data_root=data_root,
            )
        )

    def record(
        self,
        *,
        recommendation_id,
        user_id,
        day,
        structure,
        context,
        request_applied,
        candidates,
        selected,
        behavior_policy=None,
    ):

        exposure = (
            build_bandit_exposure(
                recommendation_id=(
                    recommendation_id
                ),
                user_id=user_id,
                day=day,
                structure=structure,
                context=context,
                request_applied=(
                    request_applied
                ),
                candidates=candidates,
                selected=selected,
                behavior_policy=behavior_policy,
            )
        )

        return (
            self.repository.add(
                exposure
            )
        )


__all__ = [
    "BanditDecisionLogger",
]
