import pytest
from featurevault.router import FlagRouter


def test_router_default_fallback_to_dummy():
    router = FlagRouter()
    # Unconfigured router accessing 'default' should return DummyBackend
    default_backend = router["default"]
    assert default_backend.alias == "default"


def test_router_raises_key_error_for_missing_backend():
    router = FlagRouter()
    with pytest.raises(KeyError, match="Feature flag backend 'non_existent' is not defined"):
        _ = router["non_existent"]