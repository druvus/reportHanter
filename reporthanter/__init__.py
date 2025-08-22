# reporthanter/__init__.py

# New refactored interfaces
from .core.config import DefaultConfig
from .core.exceptions import (
    ReportHanterError,
    DataProcessingError, 
    FileValidationError,
    PlotGenerationError,
    ConfigurationError,
    ReportGenerationError
)
from .report.generator import ReportGenerator

# Processors
from .processors.kraken_processor import KrakenProcessor, KrakenPlotGenerator
from .processors.kaiju_processor import KaijuProcessor, KaijuPlotGenerator  
from .processors.blast_processor import BlastProcessor, BlastPlotGenerator
from .processors.fastp_processor import FastpProcessor
from .processors.flagstat_processor import FlagstatProcessor

# Legacy compatibility (deprecated)
from .file_utils import common_suffix, paired_reads
from .fastx import fastx_file_to_df
from .kraken import wrangle_kraken, kraken_df, plot_kraken
from .blast import run_blastn, plot_blastn
from .flagstat import parse_bwa_flagstat, plot_flagstat, alignment_stats
from .fastp import parse_fastp_json, create_fastp_summary_table
from .kaiju import plot_kaiju, kaiju_db_files
from .panel_report import panel_report

__version__ = "0.2.0"
