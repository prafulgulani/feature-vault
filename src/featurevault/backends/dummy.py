from typing import Any
from featurevault.backends.base import BaseFeatureBackend


class DummyBackend(BaseFeatureBackend):
    """
    In-memory storage backend for unit testing and local development.
    """

    def __init__(self, alias: str = "dummy", **options: Any) -> None:
        super().__init__(alias=alias, **options)
        self._features: dict[str, dict[str, Any]] = options.get("FLAGS", {})

    def set_feature(self, feature_name: str, config: dict[str, Any]) -> None:
        """Helper method for unit tests to inject feature states."""
        self._features[feature_name] = config

    def clear(self) -> None:
        """Helper method to reset all features in memory."""
        self._features.clear()

    def get_feature(self, feature_name: str, default: Any = False) -> dict[str, Any]:
        if feature_name in self._features:
            return self._features[feature_name]
        return {"enabled": default, "conditions": {}, "variants": None}

    def get_all_features(self) -> dict[str, dict[str, Any]]:
        return self._features.copy()