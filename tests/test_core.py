from featurevault import feature
from featurevault.backends.dummy import DummyBackend


def test_is_enabled_returns_default_when_flag_missing():
    dummy = DummyBackend()
    feature.set_backend(dummy)

    assert feature.is_enabled("UNREGISTERED_FLAG") is False
    assert feature.is_enabled("UNREGISTERED_FLAG", default=True) is True


def test_is_enabled_respects_global_kill_switch():
    dummy = DummyBackend()
    dummy.set_feature("NEW_CHECKOUT", {"enabled": True, "conditions": {}})
    dummy.set_feature("OLD_BANNER", {"enabled": False, "conditions": {}})

    feature.set_backend(dummy)

    assert feature.is_enabled("NEW_CHECKOUT") is True
    assert feature.is_enabled("OLD_BANNER") is False


def test_is_enabled_fails_safely_on_backend_error():
    class BrokenBackend:
        def get_feature(self, feature_name, default=False):
            raise RuntimeError("Database exploded")

    feature.set_backend(BrokenBackend())  # type: ignore

    # Should handle the exception gracefully and return default False
    assert feature.is_enabled("ANY_FLAG") is False
    assert feature.is_enabled("ANY_FLAG", default=True) is True