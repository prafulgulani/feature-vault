from typing import Any
from featurevault.evaluator.hashing import is_in_rollout

def _get_context_value(key: str, context: dict[str, Any]) -> Any:
    """Safely extracts a value from the context, auto-resolving Django user objects."""
    # Direct match in context (e.g., custom attributes like "country" or "plan")
    if key in context:
        return context[key]

    # Django User Object integration
    user = context.get("user")
    if user:
        if key == "is_staff":
            return getattr(user, "is_staff", False)
        if key == "is_authenticated":
            return getattr(user, "is_authenticated", False)
        if key in ("user_id", "id", "pk"):
            return getattr(user, "pk", None)
        if key == "username":
            return getattr(user, "username", None)
        if key == "django_group":
            if hasattr(user, "groups"):
                return list(user.groups.values_list("name", flat=True))
                
    return None

def _evaluate_property(prop: dict[str, Any], context: dict[str, Any]) -> bool:
    """Evaluates a single Key/Operator/Value rule."""
    key = prop.get("key")
    operator = prop.get("operator", "exact")
    expected_value = prop.get("value")
    
    actual_value = _get_context_value(key, context)
    
    # Operator Registry
    if operator == "exact":
        return actual_value == expected_value
        
    elif operator == "is_not":
        return actual_value != expected_value
        
    elif operator == "in":
        if not isinstance(expected_value, (list, tuple)):
            return False
        # If the actual value is also a list (like Django groups), check for any intersection
        if isinstance(actual_value, (list, tuple)):
            return bool(set(actual_value).intersection(set(expected_value)))
        return actual_value in expected_value
        
    elif operator == "icontains":
        if not isinstance(actual_value, str) or not isinstance(expected_value, str):
            return False
        return expected_value.lower() in actual_value.lower()
        
    return False

def _evaluate_group(feature_name: str, group: dict[str, Any], context: dict[str, Any]) -> bool:
    """Evaluates a single group. All properties must pass (AND), then win the rollout %."""
    properties = group.get("properties", [])
    
    # AND Logic: Must pass every property in this group
    for prop in properties:
        if not _evaluate_property(prop, context):
            return False
            
    # Percentage Check: If they passed properties, do they win the rollout?
    if "rollout_percentage" in group:
        percentage = group["rollout_percentage"]
        identifier = _get_context_value("user_id", context) or context.get("ff_client_id")
        
        if not identifier or not is_in_rollout(feature_name, str(identifier), float(percentage)):
            return False
            
    return True

def evaluate_conditions(
    feature_name: str,
    conditions: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> bool:
    """
    Evaluates targeting rules using enterprise OR/AND logic.
    Groups are evaluated with OR logic. Properties inside groups use AND logic.
    """
    if not conditions:
        return True

    context = context or {}
    groups = conditions.get("groups", [])
    
    # OR Logic: If the user passes ANY group, they get the feature
    for group in groups:
        if _evaluate_group(feature_name, group, context):
            return True
            
    return False