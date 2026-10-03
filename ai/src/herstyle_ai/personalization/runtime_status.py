from pathlib import Path

from herstyle_ai.personalization.model_registry import (
    PersonalizationModelRegistry,
)

from herstyle_ai.personalization.training_guard import (
    PersonalizationTrainingGuard,
)

from herstyle_ai.personalization.bandit_exposure_repository import (
    BanditExposureRepository,
)

from herstyle_ai.personalization.feedback_repository import (
    FeedbackRepository,
)

from herstyle_ai.personalization.bandit_dataset_exporter import (
    BanditDatasetExporter,
)

from herstyle_ai.personalization.bandit_runtime import (
    SafeBanditRuntime,
)


class PersonalizationRuntimeStatus:

    def __init__(self, project_root):

        self.project_root = Path(project_root)

    def _p9_status(self):

        registry = PersonalizationModelRegistry(
            project_root=self.project_root
        )
        training_guard = PersonalizationTrainingGuard(
            project_root=self.project_root
        )

        active_version = registry.get_active_version()
        active_path = registry.get_active_model_path()

        try:
            training = training_guard.check()
        except Exception as exc:
            training = {
                "ready": False,
                "error": str(exc),
            }

        return {
            "active_model_version": active_version,
            "active_model_available": active_path is not None,
            "runtime_mode": (
                "learned_p9"
                if active_path is not None
                else "heuristic_p6"
            ),
            "training": training,
        }

    def _p10_status(self):

        runtime = SafeBanditRuntime()
        exposure_repo = BanditExposureRepository(
            project_root=self.project_root
        )
        feedback_repo = FeedbackRepository(
            project_root=self.project_root
        )
        exporter = BanditDatasetExporter(
            project_root=self.project_root
        )

        exposures = exposure_repo.list_all()
        feedback = feedback_repo.list_all()
        _, _, report = exporter.build(
            exposures=exposures,
            feedback_events=feedback,
        )

        return {
            "exploration_enabled": runtime.enabled,
            "epsilon": runtime.epsilon,
            "max_explore_candidates": (
                runtime.max_explore_candidates
            ),
            "max_score_drop": runtime.max_score_drop,
            "activation_status": runtime.activation_status,
            "total_exposures": len(exposures),
            "dataset": report,
        }

    def build(self):

        return {
            "personalization": {
                "p9": self._p9_status(),
                "p10": self._p10_status(),
            }
        }


__all__ = [
    "PersonalizationRuntimeStatus",
]
