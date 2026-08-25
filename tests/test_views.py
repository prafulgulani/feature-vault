import json
from django.test import RequestFactory
from featurevault import feature
from featurevault.backends.dummy import DummyBackend
from featurevault.middleware import FeatureContextMiddleware
from featurevault.views import user_feature_flags_view


def test_user_feature_flags_api_view():
    # dummy flags
    dummy = DummyBackend()
    dummy.set_feature("SEARCH_V2", {"enabled": True, "conditions": {}})
    dummy.set_feature("OLD_UI", {"enabled": False, "conditions": {}})
    dummy.set_feature(
        "BUTTON_COLOR",
        {
            "enabled": True,
            "conditions": {},
            "variants": {"value": "red"},
        },
    )
    feature.set_backend(dummy)

    # frontend API request simulation
    factory = RequestFactory()
    request = factory.get("/api/flags/")

    # Wrap the view in middleware so context is loaded properly
    def get_response(req):
        return user_feature_flags_view(req)

    middleware = FeatureContextMiddleware(get_response)
    response = middleware(request)

    assert response.status_code == 200
    data = json.loads(response.content)

    assert data["SEARCH_V2"]["enabled"] is True
    assert data["OLD_UI"]["enabled"] is False
    assert data["BUTTON_COLOR"]["enabled"] is True
    assert data["BUTTON_COLOR"]["variant"] == "red"