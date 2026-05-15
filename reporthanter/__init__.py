# reporthanter/__init__.py

# Core interfaces and configuration
from .core.config import DefaultConfig
from .core.exceptions import (
    ConfigurationError,
    DataProcessingError,
    FileValidationError,
    PlotGenerationError,
    ReportGenerationError,
    ReportHanterError,
)
from .processors.blast_processor import BlastPlotGenerator, BlastProcessor
from .processors.fastp_processor import FastpProcessor
from .processors.flagstat_processor import FlagstatProcessor
from .processors.kaiju_processor import KaijuPlotGenerator, KaijuProcessor

# Individual processors for advanced usage
from .processors.kraken_processor import KrakenPlotGenerator, KrakenProcessor

# Main report generator
from .report.generator import ReportGenerator

# Enhanced visualization system (new in 0.3.0+). Optional; if the
# visualization deps are not installed, these names are simply not exported.
try:
    from .visualization import (  # noqa: F401
        ChartType,
        ColorScheme,
        EnhancedReportGenerator,
        LayoutTemplate,
        VisualizationConfig,
        VisualizationConfigManager,
        create_visualization_examples,
    )
    _VISUALIZATION_AVAILABLE = True
except ImportError:
    _VISUALIZATION_AVAILABLE = False

__version__ = "0.3.0"

__all__ = [
    "DefaultConfig",
    "ConfigurationError",
    "DataProcessingError",
    "FileValidationError",
    "PlotGenerationError",
    "ReportGenerationError",
    "ReportHanterError",
    "BlastPlotGenerator",
    "BlastProcessor",
    "FastpProcessor",
    "FlagstatProcessor",
    "KaijuPlotGenerator",
    "KaijuProcessor",
    "KrakenPlotGenerator",
    "KrakenProcessor",
    "ReportGenerator",
    "create_report",
]


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
