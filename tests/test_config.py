"""
Tests for configuration management.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from reporthanter import ConfigurationError, DefaultConfig


@pytest.fixture
def default_config() -> DefaultConfig:
    """A fresh ``DefaultConfig`` for the no-file branches."""
    return DefaultConfig()


class TestDefaultConfig:
    """Test the DefaultConfig class."""

    def test_default_config_creation(self, default_config):
        assert default_config.get("plotting.width") == "container"
        assert default_config.get("filtering.kraken.level") == "species"

    def test_get_section(self, default_config):
        plotting_config = default_config.get_config("plotting")
        assert plotting_config["width"] == "container"
        assert plotting_config["height"] == 400

    def test_get_nonexistent_key(self, default_config):
        assert default_config.get("nonexistent.key", "default") == "default"
        assert default_config.get("nonexistent.key") is None

    def test_load_config_file(self, tmp_path):
        user_config = {
            "plotting": {"width": "500px", "height": 300},
            "new_section": {"new_key": "new_value"},
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(user_config))

        config = DefaultConfig(config_file)

        # Overridden by the user file.
        assert config.get("plotting.width") == "500px"
        assert config.get("plotting.height") == 300
        # Untouched defaults survive.
        assert config.get("plotting.color_scheme") == "dark2"
        # Newly introduced sections land.
        assert config.get("new_section.new_key") == "new_value"

    def test_invalid_config_file(self, tmp_path):
        config_file = tmp_path / "bad.json"
        config_file.write_text("invalid json content")

        with pytest.raises(ConfigurationError):
            DefaultConfig(config_file)

    def test_nonexistent_config_file(self):
        # The loader falls back to defaults when the file is missing
        # rather than raising; the public contract relies on that.
        config = DefaultConfig(Path("/nonexistent/config.json"))
        assert config.get("plotting.width") == "container"
