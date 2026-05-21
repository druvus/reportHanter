"""
Main report generator using MVC pattern with improved architecture.
"""

import logging
from pathlib import Path

import altair as alt
import panel as pn

from ..core.config import DefaultConfig
from ..core.exceptions import ReportGenerationError
from .sections import (
    AlignmentStatsSection,
    ContigClassificationSection,
    CoverageSection,
    RawClassificationSection,
)


class ReportGenerator:
    """Main report generator with MVC architecture."""

    def __init__(self, config: DefaultConfig | None = None):
        self.config = config or DefaultConfig()
        self.logger = logging.getLogger(self.__class__.__name__)

        # Initialize Panel extensions
        self._setup_panel()

        # Initialize sections
        self.sections = {
            "alignment": AlignmentStatsSection(self.config),
            "raw_classification": RawClassificationSection(self.config),
            "contig_classification": ContigClassificationSection(self.config),
            "coverage": CoverageSection(self.config),
        }

    def _setup_panel(self) -> None:
        """Configure Panel and Altair settings."""
        try:
            pn.extension("tabulator")
            pn.extension(
                "vega",
                sizing_mode="stretch_width",
                template=self.config.get("report.template", "fast"),
            )
            pn.widgets.Tabulator.theme = self.config.get("report.theme", "modern")

            # Altair's default data transformer caps inline data at
            # 5_000 rows, which a single high-resolution coverage trace
            # (e.g. a 250 kb reference at COVERAGE_WINDOW=50) can hit.
            # Raise the cap so the trace is never silently truncated.
            # Configurable via ``plotting.max_rows`` for callers that
            # want a tighter or looser limit.
            alt.data_transformers.enable(
                "default", max_rows=int(self.config.get("plotting.max_rows", 100_000))
            )
        except Exception as e:
            self.logger.error(f"Failed to setup Panel extensions: {e}")
            raise ReportGenerationError(f"Panel setup failed: {e}") from e

    def generate_report(
        self,
        kraken_file: str | Path,
        kaiju_table: str | Path,
        fastp_json: str | Path,
        flagstat_file: str | Path,
        mosdepth_regions: str | Path,
        blastn_files: list[str | Path] | None = None,
        blastn_file: str | Path | None = None,
        secondary_flagstat_file: str | Path | None = None,
        secondary_host: str | None = None,
        sample_name: str | None = None,
        quast_reports: list[str | Path] | None = None,
        quast_report: str | Path | None = None,
        virus_names: str | Path | None = None,
        genomad_summaries: list[str | Path] | None = None,
        genomad_summary: str | Path | None = None,
    ) -> pn.Column:
        """Generate the complete report.

        Each section is generated in its own try/except so that a failure in
        one section names that section in the resulting exception, rather
        than the generic "report generation failed" message that earlier
        versions produced.
        """

        sample_name = sample_name or "Sample"
        self.logger.info(f"Starting report generation for sample: {sample_name}")

        # Normalise single-value / list inputs. Each multi-valued
        # parameter (blastn_files, quast_reports, genomad_summaries)
        # may be passed either as a list or via its singular legacy
        # alias; the section builders always receive a list.
        blastn_paths = self._coalesce_paths(blastn_files, blastn_file)
        if not blastn_paths:
            raise ReportGenerationError(
                "generate_report requires at least one BLAST CSV "
                "(pass blastn_files=[...] or blastn_file=...)"
            )
        quast_paths = self._coalesce_paths(quast_reports, quast_report)
        genomad_paths = self._coalesce_paths(genomad_summaries, genomad_summary)

        alignment_section = self._build_section(
            "Alignment Stats",
            self.sections["alignment"].generate_section,
            flagstat_file=flagstat_file,
            fastp_json=fastp_json,
            secondary_flagstat_file=secondary_flagstat_file,
            secondary_host=secondary_host,
            quast_reports=quast_paths,
        )

        raw_classification_section = self._build_section(
            "Classification of Raw Reads",
            self.sections["raw_classification"].generate_section,
            kraken_file=kraken_file,
            kaiju_table=kaiju_table,
        )

        contig_classification_section = self._build_section(
            "Classification of Contigs",
            self.sections["contig_classification"].generate_section,
            blastn_files=blastn_paths,
            genomad_summaries=genomad_paths,
        )

        coverage_section = self._build_section(
            "Alignment Coverage",
            self.sections["coverage"].generate_section,
            mosdepth_regions=mosdepth_regions,
            virus_names=virus_names,
        )

        try:
            header = self._create_main_header(sample_name)
            main_tabs = pn.Tabs(
                ("Alignment Stats", alignment_section),
                ("Classification of Raw Reads", raw_classification_section),
                ("Classification of Contigs", contig_classification_section),
                ("Alignment Coverage", coverage_section),
                tabs_location="left",
            )
            report = pn.Column(header, pn.layout.Divider(), main_tabs)
        except Exception as e:
            self.logger.error(f"Failed to assemble final report layout: {e}")
            raise ReportGenerationError(f"Failed to assemble final report layout: {e}") from e

        self.logger.info(f"Report generation completed for sample: {sample_name}")
        return report

    @staticmethod
    def _coalesce_paths(
        plural: list[str | Path] | None,
        singular: str | Path | None,
    ) -> list[Path]:
        """Combine an optional plural list and an optional singular
        path into a single list of ``Path`` objects.

        Lets the high-level API accept either ``blastn_files=[...]``
        (the multi-assembler shape) or the legacy ``blastn_file=...``
        without surprising callers that pass both.
        """
        items: list[Path] = []
        for x in (plural or []):
            if x:
                items.append(Path(x))
        if singular:
            items.append(Path(singular))
        return items

    def _build_section(self, section_name: str, builder, **kwargs):
        """Invoke a section builder, attaching the section name to any
        exception so the failing section is identifiable in logs and CLI
        output.
        """
        try:
            return builder(**kwargs)
        except Exception as e:
            self.logger.error(f"Section '{section_name}' failed to build: {e}")
            raise ReportGenerationError(f"Section '{section_name}' failed to build: {e}") from e

    def _create_main_header(self, sample_name: str) -> pn.pane.Markdown:
        """Create the main report header."""
        return pn.pane.Markdown(
            f"""
            # ReportHanter Report
            ## Report of {sample_name}
            """,
            styles={
                "color": "white",
                "padding": "10px",
                "text-align": "center",
                "font-size": "20px",
                "background": self.config.get("report.header_bg_color", "#011a01"),
                "margin": "10px",
                "height": "185px",
            },
        )

    def save_report(
        self, report: pn.Column, output_path: str | Path, title: str | None = None
    ) -> None:
        """Save the report to an HTML file."""
        try:
            title = title or "ReportHanter Report"
            report.save(str(output_path), title=title)
            self.logger.info(f"Report saved to: {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to save report to {output_path}: {e}")
            raise ReportGenerationError(f"Failed to save report: {e}") from e
