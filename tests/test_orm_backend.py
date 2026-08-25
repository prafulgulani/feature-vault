import pytest
from featurevault import feature
from featurevault.backends.orm import ORMBackend
from featurevault.models import Feature, get_feature_model


@pytest.mark.django_db
def test_orm_backend_fetch_and_caching():
    # Create a feature in the database (No conditions attached)
    Feature.objects.create(
        name="DB_FEATURE",
        enabled=True,
    )

    orm_backend = ORMBackend()
    feature.set_backend(orm_backend)

    # First fetch populates cache from DB
    assert feature.is_enabled("DB_FEATURE") is True

    # Confirm cache key exists
    cached_val = orm_backend.cache.get("featurevault_DB_FEATURE")
    assert cached_val is not None
    assert cached_val["enabled"] is True


@pytest.mark.django_db
def test_orm_backend_cache_invalidation():
    flag = Feature.objects.create(
        name="CACHE_FLAG",
        enabled=True,
    )

    orm_backend = ORMBackend()
    feature.set_backend(orm_backend)

    # Populate cache
    assert feature.is_enabled("CACHE_FLAG") is True

    # Mutate DB record directly
    flag.enabled = False
    flag.save()

    # Invalidate cache
    orm_backend.invalidate_cache("CACHE_FLAG")

    # Evaluation MUST now reflect updated DB state
    assert feature.is_enabled("CACHE_FLAG") is False


@pytest.mark.django_db
def test_provisioning_modes(settings):
    backend = ORMBackend()
    FeatureModel = get_feature_model()

    # Mode: "off" (Default fallback, row is NOT created in DB)
    settings.FEATURE_VAULT_AUTO_PROVISION = "off"
    config_off = backend.get_feature("FLAG_OFF", default=False)
    assert config_off["enabled"] is False
    assert not FeatureModel.objects.filter(name="FLAG_OFF").exists()

    # Mode: "auto" (Row IS created automatically in DB)
    settings.FEATURE_VAULT_AUTO_PROVISION = "auto"
    config_auto = backend.get_feature("FLAG_AUTO", default=False)
    assert config_auto["enabled"] is False
    assert FeatureModel.objects.filter(name="FLAG_AUTO").exists()

    # Mode: "warn" (Row IS created and warning is logged)
    settings.FEATURE_VAULT_AUTO_PROVISION = "warn"
    config_warn = backend.get_feature("FLAG_WARN", default=False)
    assert config_warn["enabled"] is False
    assert FeatureModel.objects.filter(name="FLAG_WARN").exists()

    # Mode: "strict" (Raises KeyError when flag is missing)
    settings.FEATURE_VAULT_AUTO_PROVISION = "strict"
    with pytest.raises(KeyError) as exc_info:
        backend.get_feature("FLAG_STRICT")
    assert "FLAG_STRICT" in str(exc_info.value)