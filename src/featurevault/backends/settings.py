from typing import Any
from django.conf import settings
from featurevault.backends.base import BaseFeatureBackend


class SettingsBackend(BaseFeatureBackend):
    """
    Storage backend that reads feature flags directly from Django settings.
    """

    def __init__(self, alias: str = "settings", **options: Any) -> None:
        super().__init__(alias=alias, **options)

        # 1. Prefer explicit FLAGS passed in options (e.g., during testing)
        if "FLAGS" in options:
            self._flags_config = options["FLAGS"]
        # 2. Pull from settings only if Django is configured
        elif settings.configured:
            self._flags_config = getattr(settings, "FEATURE_FLAGS", {}).get("FLAGS", {})
        # 3. Safe fallback if Django settings are uninitialized
        else:
            self._flags_config = {}

    def get_feature(self, feature_name: str, default: Any = False) -> dict[str, Any]:
        feature_data = self._flags_config.get(feature_name)

        if feature_data is None:
            return {"enabled": default, "conditions": {}, "variants": None, "payloads": None}

        # Handle simple boolean definition: 'NEW_CHECKOUT': True
        if isinstance(feature_data, bool):
            return {"enabled": feature_data, "conditions": {}, "variants": None, "payloads": None}

        # Handle full dictionary definition
        return {
            "enabled": feature_data.get("enabled", default),
            "conditions": feature_data.get("conditions", {}),
            "variants": feature_data.get("variants"),
            "payloads": feature_data.get("payloads"),
        }

    def get_all_features(self) -> dict[str, dict[str, Any]]:
        all_features = {}
        for feature_name in self._flags_config:
            all_features[feature_name] = self.get_feature(feature_name)
        return all_features