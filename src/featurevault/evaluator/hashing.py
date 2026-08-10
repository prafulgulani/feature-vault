import hashlib


def get_bucket_value(feature_name: str, identifier: str | int) -> float:
    """
    Calculates a deterministic float value between 0.0 and 100.0
    for a given feature_name and identifier pair.
    """
    if not identifier:
        return 100.1  # Identifier missing; falls outside valid 0-100 percentage range

    key = f"{feature_name}:{identifier}".encode("utf-8")
    hash_digest = hashlib.md5(key).hexdigest()
    
    # Take first 8 hex characters and convert to integer
    hash_int = int(hash_digest[:8], 16)
    
    bucket = (hash_int / 0xFFFFFFFF) * 100.0
    return round(bucket, 2)


def is_in_rollout(feature_name: str, identifier: str | int, percentage: float | int) -> bool:
    """
    Checks if a user falls within a specific rollout percentage bucket.
    """
    if percentage <= 0:
        return False
    if percentage >= 100:
        return True

    user_bucket = get_bucket_value(feature_name, identifier)
    return user_bucket <= percentage