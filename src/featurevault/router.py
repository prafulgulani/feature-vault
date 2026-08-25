from typing import Any
from django.conf import settings
from django.utils.module_loading import import_string
from featurevault.backends.base import BaseFeatureBackend
from featurevault.backends.dummy import DummyBackend


class FlagRouter:
    """
    Central router that manages and instantiates feature flag backends
    defined in Django settings (FEATURE_FLAGS dict).
    """

    def __init__(self) -> None:
        self._backends: dict[str, BaseFeatureBackend] = {}

    def _get_config(self) -> dict[str, Any]:
        if settings.configured:
            return getattr(settings, "FEATURE_FLAGS", {})
        return {}

    def __getitem__(self, alias: str) -> BaseFeatureBackend:
        if alias in self._backends:
            return self._backends[alias]

        config = self._get_config()

        # Fallback to DummyBackend if settings aren't configured or alias isn't defined
        if alias not in config and alias == "default":
            backend_instance = DummyBackend(alias="default")
            self._backends[alias] = backend_instance
            return backend_instance

        if alias not in config:
            raise KeyError(
                f"Feature flag backend '{alias}' is not defined in FEATURE_FLAGS settings."
            )

        backend_cfg = config[alias]
        backend_cls_path = backend_cfg.get("BACKEND")
        if not backend_cls_path:
            raise ValueError(
                f"Backend configuration for '{alias}' must specify a 'BACKEND' class path."
            )

        backend_cls = import_string(backend_cls_path)
        options = backend_cfg.get("OPTIONS", {})

        backend_instance = backend_cls(alias=alias, **options)
        self._backends[alias] = backend_instance
        return backend_instance


flags = FlagRouter()