from typing import Any
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models


class BaseFeature(models.Model):
    """
    Abstract base model for feature flags.
    """

    name = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Unique identifier for the feature flag.",
    )
    enabled = models.BooleanField(
        default=False,
        help_text="Master toggle: False (Kill switch, always OFF), True (Live, evaluates conditions or ON for all if empty).",
    )
    conditions = models.JSONField(
        default=dict,
        blank=True,
        help_text="Targeting rules, user groups, or rollout percentages.",
    )
    variants = models.JSONField(
        null=True,
        blank=True,
        help_text="A/B/N testing variants and payloads.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        state = "ON" if self.enabled else "OFF"
        return f"{self.name} [{state}]"


class Feature(BaseFeature):
    """Default Feature model."""

    class Meta:
        verbose_name = "Feature Flag"
        verbose_name_plural = "Feature Flags"
        swappable = "FEATURE_FLAG_MODEL"


def get_feature_model() -> type[BaseFeature]:
    """
    Resolves the configured FEATURE_FLAG_MODEL using Django's app registry.
    Defaults to 'featurevault.Feature' if unspecified.
    """
    model_path = getattr(settings, "FEATURE_FLAG_MODEL", "featurevault.Feature")
    try:
        return apps.get_model(model_path, require_ready=False)
    except (ValueError, LookupError) as exc:
        raise ImproperlyConfigured(
            f"FEATURE_FLAG_MODEL refers to model '{model_path}' that has not been installed or does not exist."
        ) from exc