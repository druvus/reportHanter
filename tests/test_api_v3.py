"""Tests for the 0.3.0 API to ensure clean architecture works."""

from __future__ import annotations

import importlib
import inspect
import re

import pytest

from reporthanter import (
    DefaultConfig,
    KrakenProcessor,
    ReportGenerator,
    create_report,
)

# Legacy modules that were removed in 0.3.0; any successful import
# means a regression has re-introduced them.
_LEGACY_MODULES = (
    "kraken",
    "kaiju",
    "blast",
    "flagstat",
    "fastp",
    "file_utils",
    "fastx",
    "panel_report",
)

# Legacy top-level symbols that 0.3.0 removed from the package
# namespace.
_LEGACY_TOP_LEVEL = ("panel_report", "plot_kraken", "parse_fastp_json")

# Expected ``create_report`` keyword set; locked here so accidental
# rename / removal surfaces as a test failure rather than a runtime
# TypeError far downstream.
_EXPECTED_CREATE_REPORT_PARAMS = frozenset(
    {
        "blastn_files",
        "blastn_file",
        "kraken_file",
        "kaiju_table",
        "fastp_json",
        "flagstat_file",
        "mosdepth_regions",
        "secondary_flagstat_file",
        "primary_host",
        "secondary_host",
        "sample_name",
        "quast_reports",
        "quast_report",
        "virus_names",
        "genomad_summaries",
        "genomad_summary",
        "provenance_file",
        "config",
    }
)


class TestNewAPI:
    """Test the new 0.3.0 API."""

    def test_main_imports_work(self):
        assert ReportGenerator is not None
        assert DefaultConfig is not None
        assert create_report is not None
        assert KrakenProcessor is not None

    def test_report_generator_creation(self):
        config = DefaultConfig()
        generator = ReportGenerator(config)
        assert generator is not None
        assert generator.config is not None

    def test_create_report_function_signature(self):
        sig = inspect.signature(create_report)
        assert set(sig.parameters.keys()) == _EXPECTED_CREATE_REPORT_PARAMS

    def test_processors_can_be_imported_individually(self):
        from reporthanter import (
            BlastProcessor,
            FastpProcessor,
            FlagstatProcessor,
            KaijuProcessor,
            KrakenProcessor,
        )

        assert KrakenProcessor() is not None
        assert KaijuProcessor() is not None
        assert BlastProcessor() is not None
        assert FastpProcessor() is not None
        assert FlagstatProcessor() is not None

    @pytest.mark.parametrize("name", _LEGACY_TOP_LEVEL)
    def test_legacy_top_level_imports_removed(self, name):
        """Each removed legacy top-level symbol should raise ImportError."""
        import reporthanter

        assert not hasattr(reporthanter, name)

    def test_config_system_works(self):
        config = DefaultConfig()
        assert config.get("plotting.width") == "container"
        assert config.get("filtering.kraken.level") == "species"
        assert config.get("nonexistent.key") is None
        assert config.get("nonexistent.key", "default") == "default"

    def test_exceptions_are_available(self):
        from reporthanter import (
            DataProcessingError,
            FileValidationError,
            ReportHanterError,
        )

        assert issubclass(ReportHanterError, Exception)
        assert issubclass(DataProcessingError, ReportHanterError)
        assert issubclass(FileValidationError, ReportHanterError)


class TestBackwardsCompatibility:
    """Test backwards compatibility features."""

    def test_create_report_function_exists(self):
        from reporthanter import create_report

        assert create_report is not None
        assert callable(create_report)

    def test_cli_should_still_work(self):
        from reporthanter.panel_report_cli import main, parse_args

        assert parse_args is not None
        assert main is not None


class TestModuleStructure:
    """Test that the module structure is clean."""

    def test_main_package_exports(self):
        import reporthanter

        for attr in (
            "ReportGenerator",
            "DefaultConfig",
            "create_report",
            "KrakenProcessor",
            "KaijuProcessor",
            "ReportHanterError",
            "DataProcessingError",
            "__version__",
        ):
            assert hasattr(reporthanter, attr), f"missing public attr: {attr}"

    def test_version_string_looks_like_semver(self):
        """``__version__`` is read from the installed package metadata
        and so tracks ``pyproject.toml`` automatically. Assert it parses
        as a semver-ish string rather than pinning an exact value (which
        the previous test did and got 6 releases out of sync)."""
        import reporthanter

        assert isinstance(reporthanter.__version__, str)
        assert reporthanter.__version__
        assert re.match(r"^\d+\.\d+\.\d+", reporthanter.__version__), (
            f"unexpected version string: {reporthanter.__version__!r}"
        )

    @pytest.mark.parametrize("module_name", _LEGACY_MODULES)
    def test_legacy_modules_removed(self, module_name):
        """Each removed legacy submodule should fail to import."""
        with pytest.raises(ImportError):
            importlib.import_module(f"reporthanter.{module_name}")
