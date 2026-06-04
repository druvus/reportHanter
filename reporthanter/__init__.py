# reporthanter/__init__.py
from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

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
from .core.validation import validate_report_inputs
from .processors.blast_processor import BlastPlotGenerator, BlastProcessor
from .processors.coverage_processor import CoveragePlotGenerator, CoverageProcessor
from .processors.fastp_processor import FastpProcessor
from .processors.flagstat_processor import FlagstatProcessor
from .processors.genomad_processor import GenomadProcessor
from .processors.kaiju_processor import KaijuPlotGenerator, KaijuProcessor
from .processors.kraken_processor import KrakenPlotGenerator, KrakenProcessor
from .processors.quast_processor import QuastProcessor

# Main report generator
from .report.dashboard import DashboardSection
from .report.generator import ReportGenerator

# Read the version from the installed-package metadata so the
# string tracks pyproject.toml automatically; falls back to
# "0.0.0+unknown" for source-only checkouts that have not run
# `pip install -e .`.
try:
    __version__ = _pkg_version("reporthanter")
except PackageNotFoundError:  # pragma: no cover - defensive
    __version__ = "0.0.0+unknown"

__all__ = [
    "BlastPlotGenerator",
    "BlastProcessor",
    "ConfigurationError",
    "CoveragePlotGenerator",
    "CoverageProcessor",
    "DashboardSection",
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
    "validate_report_inputs",
]


def create_report(
    kraken_file: str,
    kaiju_table: str,
    fastp_json: str,
    flagstat_file: str,
    mosdepth_regions: str,
    blastn_files: list[str] | None = None,
    blastn_file: str | None = None,
    secondary_flagstat_file: str | None = None,
    primary_host: str = "Human",
    secondary_host: str | None = None,
    sample_name: str | None = None,
    quast_reports: list[str] | None = None,
    quast_report: str | None = None,
    virus_names: str | None = None,
    genomad_summaries: list[str] | None = None,
    genomad_summary: str | None = None,
    config: DefaultConfig | None = None,
) -> object:
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

    Input files are validated before report generation. A
    :exc:`~reporthanter.core.exceptions.ConfigurationError` is raised
    when any required file is absent or empty.
    """
    # Coalesce singular/plural aliases before validation so the shared
    # service always receives a flat list.
    blast_paths: list[str] = list(blastn_files or [])
    if blastn_file:
        blast_paths.append(blastn_file)
    quast_paths: list[str] = list(quast_reports or [])
    if quast_report:
        quast_paths.append(quast_report)
    genomad_paths: list[str] = list(genomad_summaries or [])
    if genomad_summary:
        genomad_paths.append(genomad_summary)

    validate_report_inputs(
        kraken_file=kraken_file,
        kaiju_table=kaiju_table,
        fastp_json=fastp_json,
        flagstat_file=flagstat_file,
        mosdepth_regions=mosdepth_regions,
        blastn_files=blast_paths,
        secondary_flagstat_file=secondary_flagstat_file,
        virus_names=virus_names,
        quast_reports=quast_paths if quast_paths else None,
        genomad_summaries=genomad_paths if genomad_paths else None,
    )

    generator = ReportGenerator(config or DefaultConfig())
    return generator.generate_report(
        # Pass the already-coalesced path lists so the generator receives
        # a single list without the singular alias duplicating any entry.
        blastn_files=blast_paths or None,  # type: ignore[arg-type]
        kraken_file=kraken_file,
        kaiju_table=kaiju_table,
        fastp_json=fastp_json,
        flagstat_file=flagstat_file,
        mosdepth_regions=mosdepth_regions,
        quast_reports=quast_paths or None,  # type: ignore[arg-type]
        virus_names=virus_names,
        genomad_summaries=genomad_paths or None,  # type: ignore[arg-type]
        secondary_flagstat_file=secondary_flagstat_file,
        primary_host=primary_host,
        secondary_host=secondary_host,
        sample_name=sample_name,
    )
