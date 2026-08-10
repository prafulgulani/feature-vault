from typing import Any
from featurevault.backends.base import BaseFeatureBackend
from featurevault.context import context as context_manager, get_current_context
from featurevault.evaluator.rules import evaluate_conditions
from featurevault.router import flags


class FeatureEvaluator:
    """
    Unified evaluation engine for feature flags, switches, and multivariate variants.
    """

    def __init__(self, backend: BaseFeatureBackend | None = None) -> None:
        self._override_backend = backend
        self.context = context_manager

    def set_backend(self, backend: BaseFeatureBackend | None) -> None:
        """Dynamically override the active backend."""
        self._override_backend = backend

    def _get_active_backend(self, backend_alias: str = "default") -> BaseFeatureBackend:
        if self._override_backend is not None:
            return self._override_backend
        return flags[backend_alias]

    def _resolve_context(self, explicit_context: dict[str, Any] | None) -> dict[str, Any]:
        """Merges implicit ContextVar context with explicitly passed kwargs."""
        resolved = get_current_context()
        if explicit_context:
            resolved.update(explicit_context)
        return resolved

    def is_enabled(
        self,
        feature_name: str,
        default: bool = False,
        backend_alias: str = "default",
        context: dict[str, Any] | None = None,
    ) -> bool:
        try:
            eval_context = self._resolve_context(context)
            active_backend = self._get_active_backend(backend_alias=backend_alias)
            
            config = active_backend.get_feature(feature_name, default=default)
            is_active = config.get("enabled", default)

            # Kill Switch
            if not is_active:
                return False

            # Conditions Check
            conditions = config.get("conditions", {})
            if not conditions:
                # Live for everyone if no conditions exist
                return True

            # Rule Matrix Evaluation
            from featurevault.evaluator.rules import evaluate_conditions
            return evaluate_conditions(feature_name, conditions, eval_context)

        except Exception:
            return default

    def get_variant(
        self,
        feature_name: str,
        default: Any = None,
        backend_alias: str = "default",
        context: dict[str, Any] | None = None,
    ) -> Any:
        """
        Multivariate evaluation call: returns a string variant or JSON payload for A/B testing.
        """
        try:
            eval_context = self._resolve_context(context)
            
            # Global gatekeeper (Kill switch and Rules)
            if not self.is_enabled(feature_name, default=False, backend_alias=backend_alias, context=eval_context):
                return default

            active_backend = self._get_active_backend(backend_alias=backend_alias)
            config = active_backend.get_feature(feature_name, default=default)
            variants = config.get("variants")

            if not variants:
                return default

            # Strict Multivariate Bucketing
            if isinstance(variants, list):
                from featurevault.evaluator.hashing import get_bucket_value
                
                # Grab a sticky identifier (User ID or Anonymous Device Cookie)
                identifier = str(eval_context.get("user_id") or eval_context.get("ff_client_id") or "")
                
                if not identifier:
                    return default  # Cannot safely bucket a completely unknown user
                
                bucket = get_bucket_value(feature_name, identifier)
                current_threshold = 0.0
                
                for variant in variants:
                    pct = float(variant.get("rollout_percentage", 0.0))
                    current_threshold += pct
                    
                    if bucket <= current_threshold:
                        return variant.get("value", default)
                        
                return default

            # Backwards compatibility for basic remote config payloads
            if isinstance(variants, dict):
                return variants.get("value", default)

            return default

        except Exception:
            return default


feature = FeatureEvaluator()