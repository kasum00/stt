from pathlib import Path

from herstyle_ai.personalization.recommendation_snapshot_repository import (
    RecommendationSnapshotRepository,
)

from herstyle_ai.personalization.bandit_exposure_repository import (
    BanditExposureRepository,
)


class RecommendationTraceabilityAudit:

    def __init__(self, project_root):

        self.project_root = Path(project_root)
        self.snapshot_repository = (
            RecommendationSnapshotRepository(
                project_root=self.project_root
            )
        )
        self.exposure_repository = (
            BanditExposureRepository(
                project_root=self.project_root
            )
        )

    def audit(self, recommendation_ids):

        recommendation_ids = [
            str(value)
            for value in recommendation_ids
            if value
        ]

        rows = []
        snapshots_found = 0
        exposures_found = 0
        both_found = 0

        for recommendation_id in recommendation_ids:

            snapshot = self.snapshot_repository.get(
                recommendation_id
            )
            exposure = self.exposure_repository.get_by_recommendation_id(
                recommendation_id
            )
            has_snapshot = snapshot is not None
            has_exposure = exposure is not None

            if has_snapshot:
                snapshots_found += 1
            if has_exposure:
                exposures_found += 1
            if has_snapshot and has_exposure:
                both_found += 1

            rows.append(
                {
                    "recommendation_id": recommendation_id,
                    "snapshot": has_snapshot,
                    "exposure": has_exposure,
                    "linked": has_snapshot and has_exposure,
                }
            )

        total = len(recommendation_ids)

        return {
            "total": total,
            "snapshots_found": snapshots_found,
            "exposures_found": exposures_found,
            "fully_linked": both_found,
            "link_rate": both_found / total if total else 0.0,
            "rows": rows,
        }


__all__ = [
    "RecommendationTraceabilityAudit",
]
