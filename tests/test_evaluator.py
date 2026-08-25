from featurevault import feature
from featurevault.backends.dummy import DummyBackend
from featurevault.evaluator.hashing import is_in_rollout, get_bucket_value


def test_sticky_hashing_consistency():
    # Same identifier + feature MUST always produce identical bucket
    bucket_1 = get_bucket_value("NEW_CHECKOUT", "user_123")
    bucket_2 = get_bucket_value("NEW_CHECKOUT", "user_123")
    assert bucket_1 == bucket_2

    # Different user produces a different bucket
    bucket_3 = get_bucket_value("NEW_CHECKOUT", "user_999")
    assert bucket_1 != bucket_3


def test_percentage_rollout_evaluation():
    dummy = DummyBackend()
    dummy.set_feature(
        "ROLLOUT_FLAG",
        {
            "enabled": True,
            "conditions": {
                "groups": [
                    {"rollout_percentage": 50}
                ]
            },
        },
    )
    feature.set_backend(dummy)

    bucket = get_bucket_value("ROLLOUT_FLAG", "user_1")
    if bucket <= 50:
        assert feature.is_enabled("ROLLOUT_FLAG", context={"user_id": "user_1"}) is True
    else:
        assert feature.is_enabled("ROLLOUT_FLAG", context={"user_id": "user_1"}) is False


def test_staff_rule_evaluation():
    class DummyUser:
        def __init__(self, is_staff: bool):
            self.is_staff = is_staff

    dummy = DummyBackend()
    dummy.set_feature(
        "STAFF_ONLY_FEATURE",
        {
            "enabled": True,
            "conditions": {
                "groups": [
                    {
                        "properties": [{"key": "is_staff", "operator": "exact", "value": True}]
                    }
                ]
            },
        },
    )
    feature.set_backend(dummy)

    staff_user = DummyUser(is_staff=True)
    normal_user = DummyUser(is_staff=False)

    assert feature.is_enabled("STAFF_ONLY_FEATURE", context={"user": staff_user}) is True
    assert feature.is_enabled("STAFF_ONLY_FEATURE", context={"user": normal_user}) is False


def test_multivariate_variant_retrieval():
    dummy = DummyBackend()
    dummy.set_feature(
        "BUTTON_COLOR",
        {
            "enabled": True,
            "conditions": {},
            "variants": {"value": "red_variant"},
        },
    )
    feature.set_backend(dummy)

    variant = feature.get_variant("BUTTON_COLOR", default="blue_variant")
    assert variant == "red_variant"
    
    
def test_strict_multivariate_bucketing():
    dummy = DummyBackend()
    dummy.set_feature(
        "MULTI_THEME",
        {
            "enabled": True,
            "conditions": {},
            "variants": [
                {"key": "light", "rollout_percentage": 30, "value": "light_mode"},
                {"key": "dark", "rollout_percentage": 30, "value": "dark_mode"},
                {"key": "neon", "rollout_percentage": 40, "value": "neon_mode"},
            ],
        },
    )
    feature.set_backend(dummy)

    # Calculate exact bucket for a test user
    bucket = get_bucket_value("MULTI_THEME", "test_user_99")
    
    # Determine the expected variant mathematically
    expected = "neon_mode"
    if bucket <= 30.0:
        expected = "light_mode"
    elif bucket <= 60.0:
        expected = "dark_mode"
        
    result = feature.get_variant("MULTI_THEME", context={"user_id": "test_user_99"})
    
    assert result == expected