"""
Tests for the 0.3.0 API to ensure clean architecture works.
"""
import pytest
import tempfile
from pathlib import Path

from reporthanter import (
    ReportGenerator,
    DefaultConfig, 
    create_report,
    KrakenProcessor,
    ReportHanterError
)


class TestNewAPI:
    """Test the new 0.3.0 API."""
    
    def test_main_imports_work(self):
        """Test that main components can be imported."""
        # This test just verifies imports work
        assert ReportGenerator is not None
        assert DefaultConfig is not None
        assert create_report is not None
        assert KrakenProcessor is not None
    
    def test_report_generator_creation(self):
        """Test ReportGenerator can be created."""
        config = DefaultConfig()
        generator = ReportGenerator(config)
        assert generator is not None
        assert generator.config is not None
    
    def test_create_report_function_signature(self):
        """Test create_report has the right signature."""
        import inspect
        sig = inspect.signature(create_report)
        
        expected_params = {
            'blastn_file', 'kraken_file', 'kaiju_table', 
            'fastp_json', 'flagstat_file', 'coverage_folder',
            'secondary_flagstat_file', 'secondary_host', 
            'sample_name', 'config'
        }
        actual_params = set(sig.parameters.keys())
        
        assert expected_params == actual_params
    
    def test_processors_can_be_imported_individually(self):
        """Test that individual processors work."""
        from reporthanter import (
            KrakenProcessor, KaijuProcessor, 
            BlastProcessor, FastpProcessor, 
            FlagstatProcessor
        )
        
        # Test they can be instantiated
        assert KrakenProcessor() is not None
        assert KaijuProcessor() is not None
        assert BlastProcessor() is not None
        assert FastpProcessor() is not None
        assert FlagstatProcessor() is not None
    
    def test_legacy_imports_removed(self):
        """Test that legacy imports are no longer available."""
        with pytest.raises(ImportError):
            from reporthanter import panel_report
        
        with pytest.raises(ImportError):
            from reporthanter import plot_kraken
            
        with pytest.raises(ImportError):
            from reporthanter import parse_fastp_json
    
    def test_config_system_works(self):
        """Test configuration system."""
        config = DefaultConfig()
        
        # Test default values
        assert config.get("plotting.width") == "container"
        assert config.get("filtering.kraken.level") == "species"
        
        # Test nonexistent keys
        assert config.get("nonexistent.key") is None
        assert config.get("nonexistent.key", "default") == "default"
    
    def test_exceptions_are_available(self):
        """Test that custom exceptions are available."""
        from reporthanter import (
            ReportHanterError, DataProcessingError, 
            FileValidationError, PlotGenerationError,
            ConfigurationError, ReportGenerationError
        )
        
        # Test they are proper Exception subclasses
        assert issubclass(ReportHanterError, Exception)
        assert issubclass(DataProcessingError, ReportHanterError)
        assert issubclass(FileValidationError, ReportHanterError)


class TestBackwardsCompatibility:
    """Test backwards compatibility features."""
    
    def test_create_report_function_exists(self):
        """Test create_report provides backwards compatibility."""
        from reporthanter import create_report
        assert create_report is not None
        assert callable(create_report)
    
    def test_cli_should_still_work(self):
        """Test CLI functionality is preserved."""
        # Import the CLI module to ensure it works
        from reporthanter.panel_report_cli import parse_args, main
        assert parse_args is not None
        assert main is not None


class TestModuleStructure:
    """Test that the module structure is clean."""
    
    def test_main_package_exports(self):
        """Test what the main package exports."""
        import reporthanter
        
        # Core components should be available
        assert hasattr(reporthanter, 'ReportGenerator')
        assert hasattr(reporthanter, 'DefaultConfig')
        assert hasattr(reporthanter, 'create_report')
        
        # Processors should be available
        assert hasattr(reporthanter, 'KrakenProcessor')
        assert hasattr(reporthanter, 'KaijuProcessor')
        
        # Exceptions should be available
        assert hasattr(reporthanter, 'ReportHanterError')
        assert hasattr(reporthanter, 'DataProcessingError')
        
        # Version should be available
        assert hasattr(reporthanter, '__version__')
        assert reporthanter.__version__ == "0.3.0"
    
    def test_legacy_modules_removed(self):
        """Test that legacy modules are gone."""
        import reporthanter
        
        # These should NOT exist anymore
        legacy_modules = [
            'kraken', 'kaiju', 'blast', 'flagstat', 
            'fastp', 'file_utils', 'fastx', 'panel_report'
        ]
        
        for module_name in legacy_modules:
            # Try to import the old module - should fail
            try:
                __import__(f'reporthanter.{module_name}')
                pytest.fail(f"Legacy module {module_name} should have been removed")
            except ImportError:
                pass  # This is expected