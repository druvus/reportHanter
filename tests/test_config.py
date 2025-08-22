"""
Tests for configuration management.
"""
import json
import tempfile
from pathlib import Path

import pytest

from reporthanter import DefaultConfig, ConfigurationError


class TestDefaultConfig:
    """Test the DefaultConfig class."""

    def test_default_config_creation(self):
        """Test creating config with defaults."""
        config = DefaultConfig()
        assert config.get("plotting.width") == "container"
        assert config.get("filtering.kraken.level") == "species"

    def test_get_section(self):
        """Test getting a specific section."""
        config = DefaultConfig()
        plotting_config = config.get_config("plotting")
        assert plotting_config["width"] == "container"
        assert plotting_config["height"] == 400

    def test_get_nonexistent_key(self):
        """Test getting a key that doesn't exist."""
        config = DefaultConfig()
        assert config.get("nonexistent.key", "default") == "default"
        assert config.get("nonexistent.key") is None

    def test_load_config_file(self):
        """Test loading configuration from file."""
        user_config = {
            "plotting": {"width": "500px", "height": 300},
            "new_section": {"new_key": "new_value"}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(user_config, f)
            config_file = Path(f.name)
        
        try:
            config = DefaultConfig(config_file)
            
            # Check merged values
            assert config.get("plotting.width") == "500px"  # Overridden
            assert config.get("plotting.height") == 300     # Overridden  
            assert config.get("plotting.color_scheme") == "dark2"  # Default preserved
            assert config.get("new_section.new_key") == "new_value"  # New value
            
        finally:
            config_file.unlink()

    def test_invalid_config_file(self):
        """Test handling of invalid JSON config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            config_file = Path(f.name)
        
        try:
            with pytest.raises(ConfigurationError):
                DefaultConfig(config_file)
        finally:
            config_file.unlink()

    def test_nonexistent_config_file(self):
        """Test handling of nonexistent config file."""
        config = DefaultConfig(Path("/nonexistent/config.json"))
        # Should fall back to defaults without error
        assert config.get("plotting.width") == "container"