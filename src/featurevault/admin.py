from typing import Any
from django.contrib import admin
from django.http import HttpRequest
from featurevault.backends.orm import ORMBackend
from featurevault.models import Feature, get_feature_model


class FeatureAdmin(admin.ModelAdmin):
    """
    Base ModelAdmin interface for managing feature flags in Django Admin.
    
    Automatically invalidates the ORMBackend cache whenever a flag is saved or deleted.
    """

    list_display = ("name", "enabled", "created_at", "updated_at")
    list_filter = ("enabled", "created_at")
    search_fields = ("name",)

    def save_model(self, request: HttpRequest, obj: Any, form: Any, change: bool) -> None:
        super().save_model(request, obj, form, change)
        # Invalidate cache on save
        ORMBackend().invalidate_cache(obj.name)

    def delete_model(self, request: HttpRequest, obj: Any) -> None:
        feature_name = obj.name
        super().delete_model(request, obj)
        # Invalidate cache on deletion
        ORMBackend().invalidate_cache(feature_name)


# Register default Feature model if using the standard model
if get_feature_model() == Feature:
    admin.site.register(Feature, FeatureAdmin)