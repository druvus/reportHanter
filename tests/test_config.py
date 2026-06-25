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

    def test_get_section_nested_dotted_path(self, default_config):
        # Regression: get_config must resolve dotted paths into nested
        # dicts the same way get() does, otherwise every per-processor
        # and filtering.* section silently resolves to {} and user
        # config overrides are ignored.
        kraken = default_config.get_config("filtering.kraken")
        assert kraken["cutoff"] == 0.001
        assert kraken["max_entries"] == 10
        assert kraken["level"] == "species"

    def test_get_section_missing_returns_empty_dict(self, default_config):
        assert default_config.get_config("filtering.does_not_exist") == {}
        # A leaf value (not a dict) must not be returned as a section.
        assert default_config.get_config("plotting.height") == {}

    def test_config_override_reaches_section(self, tmp_path):
        # An override of a nested threshold must be visible through
        # get_config so processors actually receive it.
        cfg_path = tmp_path / "override.json"
        cfg_path.write_text(json.dumps({"filtering": {"kraken": {"cutoff": 0.5}}}))
        config = DefaultConfig(cfg_path)
        assert config.get_config("filtering.kraken")["cutoff"] == 0.5

    def test_accepts_str_path(self, tmp_path):
        # The documented create_report / DefaultConfig("path.json") API
        # passes a plain string; it must not crash on `.exists()`.
        cfg_path = tmp_path / "as_str.json"
        cfg_path.write_text(json.dumps({"plotting": {"height": 123}}))
        config = DefaultConfig(str(cfg_path))
        assert config.get("plotting.height") == 123

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
