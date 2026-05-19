"""
Main report generator using MVC pattern with improved architecture.
"""

import logging
from pathlib import Path

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
        """Configure Panel settings."""
        try:
            pn.extension("tabulator")
            pn.extension(
                "vega",
                sizing_mode="stretch_width",
                template=self.config.get("report.template", "fast"),
            )
            pn.widgets.Tabulator.theme = self.config.get("report.theme", "modern")
        except Exception as e:
            self.logger.error(f"Failed to setup Panel extensions: {e}")
            raise ReportGenerationError(f"Panel setup failed: {e}") from e

    def generate_report(
        self,
        blastn_file: str | Path,
        kraken_file: str | Path,
        kaiju_table: str | Path,
        fastp_json: str | Path,
        flagstat_file: str | Path,
        coverage_folder: str | Path | None = None,
        secondary_flagstat_file: str | Path | None = None,
        secondary_host: str | None = None,
        sample_name: str | None = None,
        mosdepth_regions: str | Path | None = None,
    ) -> pn.Column:
        """Generate the complete report.

        Each section is generated in its own try/except so that a failure in
        one section names that section in the resulting exception, rather
        than the generic "report generation failed" message that earlier
        versions produced.
        """

        sample_name = sample_name or "Sample"
        self.logger.info(f"Starting report generation for sample: {sample_name}")

        alignment_section = self._build_section(
            "Alignment Stats",
            self.sections["alignment"].generate_section,
            flagstat_file=flagstat_file,
            fastp_json=fastp_json,
            secondary_flagstat_file=secondary_flagstat_file,
            secondary_host=secondary_host,
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
            blastn_file=blastn_file,
        )

        coverage_section = self._build_section(
            "Alignment Coverage",
            self.sections["coverage"].generate_section,
            coverage_folder=coverage_folder,
            mosdepth_regions=mosdepth_regions,
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
