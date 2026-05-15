"""
Configuration management for reportHanter.
"""
import copy
import json
import logging
from pathlib import Path
from typing import Any

from .exceptions import ConfigurationError
from .interfaces import ConfigProvider


class DefaultConfig(ConfigProvider):
    """Default configuration provider with sensible defaults."""

    DEFAULT_CONFIG = {
        "plotting": {
            "width": "container",
            "height": 400,
            "color_scheme": "dark2"
        },
        "filtering": {
            "kraken": {
                "level": "species",
                "cutoff": 0.01,
                "max_entries": 10,
                "virus_only": True
            },
            "kaiju": {
                "cutoff": 0.01,
                "max_entries": 10
            }
        },
        "report": {
            "template": "fast",
            "theme": "modern",
            "header_color": "#04c273",
            "header_bg_color": "#011a01"
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        }
    }

    def __init__(self, config_file: Path | None = None):
        # deepcopy so per-instance mutations don't leak into DEFAULT_CONFIG
        self.config = copy.deepcopy(self.DEFAULT_CONFIG)
        if config_file and config_file.exists():
            self._load_config_file(config_file)

    def _load_config_file(self, config_file: Path) -> None:
        """Load configuration from JSON file."""
        try:
            with open(config_file) as f:
                user_config = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            raise ConfigurationError(f"Failed to load config file {config_file}: {e}") from e

        self._validate_against_schema(user_config, self.DEFAULT_CONFIG, path="")
        self._merge_config(self.config, user_config)

    def _validate_against_schema(
        self,
        user: dict[str, Any],
        schema: dict[str, Any],
        path: str,
    ) -> None:
        """Warn loudly when the user config contains keys that are not known
        in the default schema. Unknown keys are not an error (forward
        compatibility), but they are logged at WARNING so typos are visible.
        """
        logger = logging.getLogger(__name__)
        if not isinstance(user, dict):
            return
        for key, value in user.items():
            dotted = f"{path}.{key}" if path else key
            if key not in schema:
                logger.warning(
                    "Unknown configuration key %r (no such key in the "
                    "DefaultConfig schema)", dotted
                )
                continue
            if isinstance(schema[key], dict) and isinstance(value, dict):
                self._validate_against_schema(value, schema[key], dotted)

    def _merge_config(self, base: dict[str, Any], update: dict[str, Any]) -> None:
        """Recursively merge configuration dictionaries."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get_config(self, section: str | None = None) -> dict[str, Any]:
        """Get configuration dictionary."""
        if section:
            return self.config.get(section, {})
        return self.config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a specific configuration value using dot notation."""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default