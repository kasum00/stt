import hashlib
import json

from dataclasses import fields
from pathlib import Path
from typing import Any, Dict, Optional

from herstyle_ai.personalization.preference_profile import (
    UserPreferenceProfile,
)


class PreferenceRepository:
    """Persist one preference profile JSON file per user."""

    def __init__(
        self,
        project_root: Path,
        data_root: Path | None = None,
    ):
        self.project_root = Path(project_root)
        self.data_root = Path(data_root) if data_root is not None else self.project_root / "data"
        self.profile_dir = (
            self.data_root
            / "processed"
            / "personalization"
            / "profiles"
        )
        self.profile_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    @staticmethod
    def user_hash(
        user_id: str,
    ) -> str:
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError(
                "user_id must be a non-empty string"
            )

        return hashlib.sha256(
            user_id.encode("utf-8")
        ).hexdigest()

    @classmethod
    def _user_hash(
        cls,
        user_id: str,
    ) -> str:
        return cls.user_hash(user_id)

    def profile_path(
        self,
        user_id: str,
    ) -> Path:
        return self.profile_dir / (
            f"{self.user_hash(user_id)}.json"
        )

    def _profile_path(
        self,
        user_id: str,
    ) -> Path:
        return self.profile_path(user_id)

    def save(
        self,
        profile: UserPreferenceProfile,
    ) -> Dict[str, Any]:
        if not isinstance(
            profile,
            UserPreferenceProfile,
        ):
            raise TypeError(
                "profile must be a UserPreferenceProfile"
            )

        payload = profile.to_dict()
        path = self.profile_path(profile.user_id)
        temporary_path = path.with_suffix(".tmp")

        with temporary_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                payload,
                file,
                ensure_ascii=False,
                indent=2,
            )
            file.write("\n")

        temporary_path.replace(path)
        return payload

    def load(
        self,
        user_id: str,
    ) -> Optional[UserPreferenceProfile]:
        path = self.profile_path(user_id)

        if not path.exists():
            return None

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            payload = json.load(file)

        if not isinstance(payload, dict):
            raise ValueError(
                "stored preference profile must be a JSON object"
            )

        profile_fields = {
            field.name
            for field in fields(UserPreferenceProfile)
        }
        profile_data = {
            key: value
            for key, value in payload.items()
            if key in profile_fields
        }
        profile_data["user_id"] = user_id

        return UserPreferenceProfile(
            **profile_data
        )

    def exists(
        self,
        user_id: str,
    ) -> bool:
        return self.profile_path(user_id).exists()


__all__ = [
    "PreferenceRepository",
]
