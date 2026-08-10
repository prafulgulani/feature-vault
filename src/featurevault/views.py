from django.http import HttpRequest, JsonResponse
from featurevault import feature


def user_feature_flags_view(request: HttpRequest) -> JsonResponse:
    """
    Returns a JSON payload of all feature flags evaluated for the current user.
    """

    active_backend = feature._get_active_backend()
    all_features = active_backend.get_all_features()

    result = {}
    for feature_name, config in all_features.items():
        is_on = feature.is_enabled(feature_name)

        if is_on and config.get("variants"):
            variant = feature.get_variant(feature_name)
            result[feature_name] = {"enabled": True, "variant": variant}
        else:
            result[feature_name] = {"enabled": is_on}

    return JsonResponse(result)