from django.http import HttpResponse
from django.test import RequestFactory
from featurevault import feature
from featurevault.backends.dummy import DummyBackend
from featurevault.context import clear_current_context, get_current_context
from featurevault.middleware import FeatureContextMiddleware


def test_context_manager_sets_and_cleans_context():
    clear_current_context()
    assert get_current_context() == {}

    with feature.context(user_id="user_99", is_staff=True):
        ctx = get_current_context()
        assert ctx["user_id"] == "user_99"
        assert ctx["is_staff"] is True

    # Confirm context is cleaned up after block exits
    assert get_current_context() == {}


def test_implicit_context_evaluation_with_context_manager():
    dummy = DummyBackend()
    dummy.set_feature(
        "STAFF_FEATURE",
        {
            "enabled": True, 
            "conditions": {
                "groups": [
                    {
                        "properties": [{"key": "is_staff", "operator": "exact", "value": True}]
                    }
                ]
            }
        },
    )
    feature.set_backend(dummy)

    # Without passing context into is_enabled directly!
    with feature.context(is_staff=True):
        assert feature.is_enabled("STAFF_FEATURE") is True

    with feature.context(is_staff=False):
        assert feature.is_enabled("STAFF_FEATURE") is False


def test_middleware_captures_request_and_sets_cookie():
    factory = RequestFactory()
    request = factory.get("/home/")

    def dummy_view(req):
        # Inside view execution, implicit context MUST be available
        assert get_current_context()["request"] == req
        return HttpResponse("OK")

    middleware = FeatureContextMiddleware(dummy_view)
    response = middleware(request)

    assert response.status_code == 200
    # Confirm anonymous device cookie is attached to response
    assert "ff_client_id" in response.cookies