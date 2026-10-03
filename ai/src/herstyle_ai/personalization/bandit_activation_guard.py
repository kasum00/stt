import os


class BanditExplorationGuard:

    def __init__(
        self,
        *,
        max_epsilon=0.05,
    ):

        self.max_epsilon = float(max_epsilon)

    @staticmethod
    def _enabled_env():

        return os.getenv(
            "HERSTYLE_BANDIT_EXPLORATION_ENABLED",
            "0",
        ).strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    def check(self, *, epsilon, enabled=None):

        blockers = []

        if enabled is None:
            enabled = self._enabled_env()

        enabled = bool(enabled)

        if not enabled:
            blockers.append(
                "exploration_feature_flag_disabled"
            )

        try:
            epsilon = float(epsilon)
        except (TypeError, ValueError):
            epsilon = None
            blockers.append("invalid_epsilon")

        if (
            epsilon is not None
            and (
                epsilon < 0.0
                or epsilon > self.max_epsilon
            )
        ):
            blockers.append(
                "epsilon_outside_safe_range"
            )

        return {
            "allowed": len(blockers) == 0,
            "requested_enabled": enabled,
            "epsilon": epsilon,
            "max_epsilon": self.max_epsilon,
            "blockers": blockers,
        }


__all__ = [
    "BanditExplorationGuard",
]
