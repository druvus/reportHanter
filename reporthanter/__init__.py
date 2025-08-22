# reporthanter/__init__.py

# Core interfaces and configuration
from .core.config import DefaultConfig
from .core.exceptions import (
    ReportHanterError,
    DataProcessingError, 
    FileValidationError,
    PlotGenerationError,
    ConfigurationError,
    ReportGenerationError
)

# Main report generator
from .report.generator import ReportGenerator

# Individual processors for advanced usage
from .processors.kraken_processor import KrakenProcessor, KrakenPlotGenerator
from .processors.kaiju_processor import KaijuProcessor, KaijuPlotGenerator  
from .processors.blast_processor import BlastProcessor, BlastPlotGenerator
from .processors.fastp_processor import FastpProcessor
from .processors.flagstat_processor import FlagstatProcessor

# Enhanced visualization system (new in 0.3.0+)
try:
    from .visualization import (
        EnhancedReportGenerator,
        VisualizationConfig, VisualizationConfigManager,
        ChartType, ColorScheme, LayoutTemplate,
        create_visualization_examples
    )
    _VISUALIZATION_AVAILABLE = True
except ImportError:
    # Graceful fallback if visualization dependencies not available
    _VISUALIZATION_AVAILABLE = False

__version__ = "0.3.0"

# Convenience function for backwards compatibility
def create_report(blastn_file, kraken_file, kaiju_table, fastp_json, 
                 flagstat_file, coverage_folder, secondary_flagstat_file=None,
                 secondary_host=None, sample_name=None, config=None):
    """
    Convenience function that mimics the old panel_report API.
    
    This provides a smooth transition path for users upgrading from 0.2.x.
    """
    generator = ReportGenerator(config or DefaultConfig())
    return generator.generate_report(
        blastn_file=blastn_file,
        kraken_file=kraken_file, 
        kaiju_table=kaiju_table,
        fastp_json=fastp_json,
        flagstat_file=flagstat_file,
        coverage_folder=coverage_folder,
        secondary_flagstat_file=secondary_flagstat_file,
        secondary_host=secondary_host,
        sample_name=sample_name
    )
