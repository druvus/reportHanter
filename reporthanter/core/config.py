"""
Configuration management for reportHanter.
"""
from typing import Any, Dict, Optional
from pathlib import Path
import json
from .interfaces import ConfigProvider
from .exceptions import ConfigurationError


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
    
    def __init__(self, config_file: Optional[Path] = None):
        self.config = self.DEFAULT_CONFIG.copy()
        if config_file and config_file.exists():
            self._load_config_file(config_file)
    
    def _load_config_file(self, config_file: Path) -> None:
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                self._merge_config(self.config, user_config)
        except (json.JSONDecodeError, IOError) as e:
            raise ConfigurationError(f"Failed to load config file {config_file}: {e}")
    
    def _merge_config(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """Recursively merge configuration dictionaries."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get_config(self, section: Optional[str] = None) -> Dict[str, Any]:
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