from featurevault.backends.dummy import DummyBackend
from featurevault.backends.settings import SettingsBackend


def test_dummy_backend_set_and_clear():
    dummy = DummyBackend()
    dummy.set_feature("SEARCH_V2", {"enabled": True})

    assert dummy.get_feature("SEARCH_V2")["enabled"] is True

    dummy.clear()
    assert dummy.get_feature("SEARCH_V2")["enabled"] is False


def test_settings_backend_handles_booleans_and_dicts():
    settings_backend = SettingsBackend(
        FLAGS={
            "BOOLEAN_FLAG": True,
            "FULL_DICT_FLAG": {"enabled": False, "conditions": {"is_staff": True}},
        }
    )

    bool_res = settings_backend.get_feature("BOOLEAN_FLAG")
    assert bool_res["enabled"] is True

    dict_res = settings_backend.get_feature("FULL_DICT_FLAG")
    assert dict_res["enabled"] is False
    assert dict_res["conditions"] == {"is_staff": True}