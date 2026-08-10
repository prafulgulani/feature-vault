import logging
from typing import Any
from django.conf import settings
from django.core.cache import caches
from django.db.models import Q
from featurevault.backends.base import BaseFeatureBackend
from featurevault.models import get_feature_model


logger = logging.getLogger("featurevault")


class ORMBackend(BaseFeatureBackend):
    """
    Storage backend that fetches feature configurations from relational database tables 
    via the Django ORM, backed by django.core.cache to prevent repetitive database queries.
    """

    def __init__(self, alias: str = "orm", **options: Any) -> None:
        super().__init__(alias=alias, **options)
        self.cache_alias = options.get("CACHE_ALIAS", "default")
        self.cache_timeout = options.get("CACHE_TIMEOUT", 300)
        self.cache_prefix = options.get("CACHE_PREFIX", "featurevault_")

    @property
    def cache(self):
        return caches[self.cache_alias]

    def _get_cache_key(self, feature_name: str) -> str:
        return f"{self.cache_prefix}{feature_name}"

    def get_feature(self, feature_name: str, default: Any = None) -> dict[str, Any]:
        # 1. Check cache first
        cache_key = self._get_cache_key(feature_name)
        cached_data = self.cache.get(cache_key)

        if cached_data is not None:
            return cached_data

        FeatureModel = get_feature_model()
        
        # Pull provisioning mode setting (Support legacy boolean or string)
        raw_mode = getattr(settings, "FEATURE_VAULT_AUTO_PROVISION", "off")
        if isinstance(raw_mode, bool):
            mode = "auto" if raw_mode else "off"
        else:
            mode = str(raw_mode).lower()

        try:
            if mode in ("auto", "warn"):
                # Fetch existing, or safely insert missing flag into DB
                obj, created = FeatureModel.objects.get_or_create(
                    name=feature_name,
                    defaults={
                        "enabled": False,
                        "conditions": {},
                        "variants": None,
                    },
                )
                if created and mode == "warn":
                    logger.warning(
                        "Auto-provisioned missing feature flag '%s' in database (enabled=False).",
                        feature_name,
                    )
            elif mode == "strict":
                # Strict mode: Raise KeyError if the flag is missing from DB
                obj = FeatureModel.objects.get(name=feature_name)
            else:
                # "off" mode (or default): Standard DB lookup
                obj = FeatureModel.objects.get(name=feature_name)

            data = {
                "enabled": obj.enabled,
                "conditions": obj.conditions or {},
                "variants": obj.variants,
            }

        except FeatureModel.DoesNotExist:
            if mode == "strict":
                raise KeyError(
                    f"Feature flag '{feature_name}' does not exist in database and FEATURE_VAULT_AUTO_PROVISION is 'strict'."
                )
            
            fallback = default if default is not None else False
            data = {"enabled": fallback, "conditions": {}, "variants": None}

        # Save to cache
        self.cache.set(cache_key, data, timeout=self.cache_timeout)
        return data

    def get_all_features(self) -> dict[str, dict[str, Any]]:
        model = get_feature_model()
        features = {}
        for obj in model.objects.all():
            data = {
                "enabled": obj.enabled,
                "conditions": obj.conditions or {},
                "variants": obj.variants,
            }
            features[obj.name] = data
            # Populate individual caches during bulk fetch
            self.cache.set(self._get_cache_key(obj.name), data, timeout=self.cache_timeout)
        return features

    def invalidate_cache(self, feature_name: str) -> None:
        """Clears the cached record for a specific feature."""
        self.cache.delete(self._get_cache_key(feature_name))