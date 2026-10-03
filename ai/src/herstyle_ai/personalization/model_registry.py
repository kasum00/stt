import json

from datetime import (
    datetime,
    timezone,
)

from pathlib import Path

from herstyle_ai.personalization.candidate_acceptance import (
    PersonalizationCandidateAcceptance,
)


class PersonalizationModelRegistry:

    def __init__(
        self,
        project_root,
    ):

        self.project_root = Path(
            project_root
        )

        self.model_dir = (
            self.project_root
            / "data"
            / "processed"
            / "personalization"
            / "models"
        )

        self.model_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.registry_path = (
            self.model_dir
            / "active_model.json"
        )

        self.acceptance_policy = (
            PersonalizationCandidateAcceptance()
        )

    @staticmethod
    def _default_state():

        return {
            "active_version": None,
            "activated_at": None,
            "history": [],
        }

    def load(self):

        if not self.registry_path.is_file():

            return self._default_state()

        try:

            with self.registry_path.open(
                "r",
                encoding="utf-8",
            ) as f:

                state = json.load(
                    f
                )

        except (
            OSError,
            json.JSONDecodeError,
        ) as exc:

            raise RuntimeError(
                "Active model registry is invalid"
            ) from exc

        if not isinstance(
            state,
            dict,
        ):

            raise RuntimeError(
                "Active model registry must contain an object"
            )

        return {
            "active_version": state.get(
                "active_version"
            ),
            "activated_at": state.get(
                "activated_at"
            ),
            "history": state.get(
                "history",
                [],
            )
            if isinstance(
                state.get(
                    "history",
                    [],
                ),
                list,
            )
            else [],
        }

    def _write(
        self,
        state,
    ):

        with self.registry_path.open(
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                state,
                f,
                ensure_ascii=False,
                indent=2,
            )

            f.write(
                "\n"
            )

    def get_active_version(
        self,
    ):

        return self.load().get(
            "active_version"
        )

    def get_active_model_path(
        self,
    ):

        version = self.get_active_version()

        if not version:

            return None

        path = (
            self.model_dir
            / f"{version}.joblib"
        )

        if not path.is_file():

            return None

        return str(
            path
        )

    def _metadata_path(
        self,
        version,
    ):

        return (
            self.model_dir
            / f"{str(version)}.metadata.json"
        )

    def _load_metadata(
        self,
        version,
    ):

        metadata_path = self._metadata_path(
            version
        )

        if not metadata_path.is_file():

            raise RuntimeError(
                "Model metadata not found: "
                + str(
                    metadata_path
                )
            )

        try:

            with metadata_path.open(
                "r",
                encoding="utf-8",
            ) as f:

                metadata = json.load(
                    f
                )

        except (
            OSError,
            json.JSONDecodeError,
        ) as exc:

            raise RuntimeError(
                "Model metadata is invalid"
            ) from exc

        if not isinstance(
            metadata,
            dict,
        ):

            raise RuntimeError(
                "Model metadata must contain an object"
            )

        return metadata

    def activate(
        self,
        version,
    ):

        version = str(
            version
        )

        if version == "p9-logreg-smoke-test":

            raise RuntimeError(
                "Smoke-test model cannot be activated"
            )

        model_path = (
            self.model_dir
            / f"{version}.joblib"
        )

        if not model_path.is_file():

            raise RuntimeError(
                "Model artifact not found: "
                + str(
                    model_path
                )
            )

        metadata = self._load_metadata(
            version
        )

        evaluation = metadata.get(
            "evaluation",
            {},
        )

        acceptance = self.acceptance_policy.evaluate(
            evaluation
        )

        if not acceptance[
            "accepted"
        ]:

            raise RuntimeError(
                "Personalization candidate rejected: "
                + ", ".join(
                    acceptance[
                        "blockers"
                    ]
                )
            )

        state = self.load()

        activated_at = datetime.now(
            timezone.utc
        ).isoformat()

        history = list(
            state.get(
                "history",
                [],
            )
        )

        history.append(
            {
                "version": version,
                "activated_at": activated_at,
                "acceptance": acceptance,
            }
        )

        state = {
            "active_version": version,
            "activated_at": activated_at,
            "history": history,
        }

        self._write(
            state
        )

        return {
            **state,
            "model_path": str(
                model_path
            ),
            "metadata_path": str(
                self._metadata_path(
                    version
                )
            ),
            "acceptance": acceptance,
        }

    def deactivate(
        self,
    ):

        state = self.load()

        state[
            "active_version"
        ] = None

        state[
            "activated_at"
        ] = None

        self._write(
            state
        )

        return state


__all__ = [
    "PersonalizationModelRegistry",
]
