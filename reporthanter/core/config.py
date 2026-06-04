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
    """Default configuration provider with sensible defaults.

    .. rubric:: Threshold precedence

    Filtering thresholds (cutoff, max_entries, level, virus_only) are
    defined in two places: here as ``DEFAULT_CONFIG`` values and as
    method-signature defaults on each processor's ``filter_data``
    method.  The two sets of values **must be kept identical**; the
    method defaults exist only so that the processors work correctly
    when called without a config object (e.g. in unit tests or
    standalone scripts).

    When the report pipeline calls ``filter_data`` it always passes
    the relevant config dict as keyword arguments, so the **config
    values take precedence** over the method defaults.  Concretely,
    ``sections.py`` does::

        kraken_config = self.config.get_config("filtering.kraken")
        processor.filter_data(data, **kraken_config)

    meaning that if you add a new threshold or change a default,
    update *both* ``DEFAULT_CONFIG`` below *and* the method signature
    in the corresponding processor.
    """

    DEFAULT_CONFIG = {
        "plotting": {
            "width": "container",
            "height": 400,
            "color_scheme": "dark2",
            # Height of each bar in the Kraken, Kaiju and BLAST bar charts
            # (in pixels, passed as alt.Step).  Increase this value to make
            # bars taller; decrease it for more compact charts.
            "bar_step_px": 22,
        },
        "filtering": {
            # Kraken thresholds.  Mirror the defaults in
            # KrakenProcessor.filter_data; keep both in sync.
            "kraken": {"level": "species", "cutoff": 0.001, "max_entries": 10, "virus_only": True},
            # Kaiju thresholds.  Mirror the defaults in
            # KaijuProcessor.filter_data; keep both in sync.
            "kaiju": {"cutoff": 0.01, "max_entries": 10},
            # Minimum percentage of reads (or breadth) required for a hit to
            # appear on the Dashboard landing cards.  Applied to:
            #   - Kraken top-5 card (% of reads)
            #   - Kaiju top-5 card  (% of reads)
            #   - Coverage card     (% bp >= 5x)
            "dashboard_min_pct": 1.0,
        },
        "report": {
            "template": "fast",
            "theme": "modern",
            # Brand palette taken from the reportHanter wordmark:
            # navy (#102D5F) for primary text + accents, teal
            # (#13B5A6) for secondary highlights. Section banners are
            # white with a teal left rule + navy text so the report
            # reads as a clean light-themed dashboard rather than the
            # earlier dark-green bands. Override any of these in a
            # user config file to recolour the rendered HTML.
            "primary_color": "#102D5F",
            "accent_color": "#13B5A6",
            "header_color": "#102D5F",
            "header_bg_color": "#ffffff",
        },
        "logging": {"level": "INFO", "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
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
        user: Any,
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
                    "Unknown configuration key %r (no such key in the DefaultConfig schema)", dotted
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
            return self.config.get(section, {})  # type: ignore[return-value]
        return self.config

    def get(self, key: str, default: Any = None) -> Any:
        """Get a specific configuration value using dot notation."""
        keys = key.split(".")
        value: Any = self.config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
