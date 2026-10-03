from pathlib import Path

from herstyle_ai.personalization.runtime_status import (
    PersonalizationRuntimeStatus,
)


class ProductionSafetyChecker:

    def __init__(self, project_root):

        self.project_root = Path(project_root)

    def check(self):

        status = PersonalizationRuntimeStatus(
            project_root=self.project_root
        ).build()

        p9 = status["personalization"]["p9"]
        p10 = status["personalization"]["p10"]

        warnings = []
        errors = []

        active_version = p9.get(
            "active_model_version"
        )
        active_available = bool(
            p9.get("active_model_available")
        )

        if active_version and not active_available:
            errors.append(
                "p9_registry_points_to_missing_model"
            )

        if p10.get("exploration_enabled"):
            warnings.append(
                "bandit_exploration_is_enabled"
            )

        epsilon = float(
            p10.get("epsilon", 0.0) or 0.0
        )

        if epsilon > 0.05:
            errors.append(
                "bandit_epsilon_exceeds_safety_cap"
            )

        p9_training = p9.get("training") or {}

        if not p9_training.get("ready", False):
            warnings.append(
                "p9_training_data_not_ready"
            )

        p10_dataset = p10.get("dataset") or {}

        if not p10_dataset.get(
            "ready_for_bandit_training",
            False,
        ):
            warnings.append(
                "p10_bandit_data_not_ready"
            )

        return {
            "safe": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "status": status,
        }


__all__ = [
    "ProductionSafetyChecker",
]
