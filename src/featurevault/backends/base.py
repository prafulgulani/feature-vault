import abc
from typing import Any


class BaseFeatureBackend(abc.ABC):
    """
    Abstract Base Class that all feature flag storage engines must implement.
    """

    def __init__(self, alias: str = "default", **options: Any) -> None:
        self.alias = alias
        self.options = options

    @abc.abstractmethod
    def get_feature(self, feature_name: str, default: Any = False) -> dict[str, Any]:
        """
        Fetch feature configuration dictionary by name.
        
        Must return a dict containing at minimum:
        {
            "enabled": bool,
            "conditions": dict,
            "variants": dict | None
        }
        """
        pass

    @abc.abstractmethod
    def get_all_features(self) -> dict[str, dict[str, Any]]:
        """
        Fetch all feature definitions for bulk evaluation.
        Returns a mapping of feature_name -> feature_config_dict.
        """
        pass