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
from .processors.coverage_processor import CoveragePlotGenerator, CoverageProcessor
from .processors.fastp_processor import FastpProcessor
from .processors.flagstat_processor import FlagstatProcessor
from .processors.genomad_processor import GenomadProcessor
from .processors.kaiju_processor import KaijuPlotGenerator, KaijuProcessor
from .processors.kraken_processor import KrakenPlotGenerator, KrakenProcessor
from .processors.quast_processor import QuastProcessor

# Main report generator
from .report.generator import ReportGenerator

__version__ = "0.5.7"

__all__ = [
    "BlastPlotGenerator",
    "BlastProcessor",
    "ConfigurationError",
    "CoveragePlotGenerator",
    "CoverageProcessor",
    "DataProcessingError",
    "DefaultConfig",
    "FastpProcessor",
    "FileValidationError",
    "FlagstatProcessor",
    "GenomadProcessor",
    "KaijuPlotGenerator",
    "KaijuProcessor",
    "KrakenPlotGenerator",
    "KrakenProcessor",
    "PlotGenerationError",
    "QuastProcessor",
    "ReportGenerationError",
    "ReportGenerator",
    "ReportHanterError",
    "create_report",
]


def create_report(
    kraken_file,
    kaiju_table,
    fastp_json,
    flagstat_file,
    mosdepth_regions,
    blastn_files=None,
    blastn_file=None,
    secondary_flagstat_file=None,
    secondary_host=None,
    sample_name=None,
    quast_reports=None,
    quast_report=None,
    virus_names=None,
    genomad_summaries=None,
    genomad_summary=None,
    config=None,
):
    """High-level wrapper around :class:`ReportGenerator`.

    Produces a single self-contained HTML report for one sample.
    From v0.5.0 the BLAST, QUAST and geNomad inputs are accepted as
    lists (``blastn_files``, ``quast_reports``, ``genomad_summaries``)
    so the report can carry one row per (sample, assembler). The
    singular ``blastn_file`` / ``quast_report`` / ``genomad_summary``
    parameters remain accepted for backwards compatibility with
    single-assembler callers.

    Coverage is sourced from a mosdepth ``regions.bed.gz``; the
    legacy ``coverage_folder`` parameter from 0.2.x was removed when
    virusHanter2 retired its bam2plot rule.
    """
    generator = ReportGenerator(config or DefaultConfig())
    return generator.generate_report(
        blastn_files=blastn_files,
        blastn_file=blastn_file,
        kraken_file=kraken_file,
        kaiju_table=kaiju_table,
        fastp_json=fastp_json,
        flagstat_file=flagstat_file,
        mosdepth_regions=mosdepth_regions,
        quast_reports=quast_reports,
        quast_report=quast_report,
        virus_names=virus_names,
        genomad_summaries=genomad_summaries,
        genomad_summary=genomad_summary,
        secondary_flagstat_file=secondary_flagstat_file,
        secondary_host=secondary_host,
        sample_name=sample_name,
    )
