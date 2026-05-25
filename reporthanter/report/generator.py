"""
Main report generator using MVC pattern with improved architecture.
"""

import base64
import logging
from importlib import resources
from pathlib import Path

import altair as alt
import panel as pn

from ..core.config import DefaultConfig
from ..core.exceptions import ReportGenerationError
from .dashboard import DashboardSection
from .sections import (
    AssemblySection,
    ContigClassificationSection,
    CoverageSection,
    HostAlignmentSection,
    RawClassificationSection,
    ReadStatisticsSection,
)


class ReportGenerator:
    """Main report generator with MVC architecture."""

    def __init__(self, config: DefaultConfig | None = None):
        self.config = config or DefaultConfig()
        self.logger = logging.getLogger(self.__class__.__name__)

        # Initialize Panel extensions
        self._setup_panel()

        # Initialize sections. The pipeline's data-flow order is
        # used both for the section build order below and for the
        # main_tabs layout: read QC → host alignment → read-level
        # classification → assembly metrics → contig classification
        # → per-reference coverage.
        self.sections = {
            "dashboard": DashboardSection(self.config),
            "read_statistics": ReadStatisticsSection(self.config),
            "host_alignment": HostAlignmentSection(self.config),
            "raw_classification": RawClassificationSection(self.config),
            "assembly": AssemblySection(self.config),
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
        primary_host: str = "Human",
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

        dashboard_section = self._build_section(
            "Dashboard",
            self.sections["dashboard"].generate_section,
            sample_name=sample_name,
            fastp_json=fastp_json,
            flagstat_file=flagstat_file,
            kraken_file=kraken_file,
            kaiju_table=kaiju_table,
            blastn_files=blastn_paths,
            quast_reports=quast_paths,
            mosdepth_regions=mosdepth_regions,
            virus_names=virus_names,
        )

        read_statistics_section = self._build_section(
            "Read statistics",
            self.sections["read_statistics"].generate_section,
            fastp_json=fastp_json,
        )

        host_alignment_section = self._build_section(
            "Host alignment",
            self.sections["host_alignment"].generate_section,
            flagstat_file=flagstat_file,
            secondary_flagstat_file=secondary_flagstat_file,
            primary_host=primary_host,
            secondary_host=secondary_host,
        )

        raw_classification_section = self._build_section(
            "Classification of reads",
            self.sections["raw_classification"].generate_section,
            kraken_file=kraken_file,
            kaiju_table=kaiju_table,
        )

        # QUAST sits in its own Assembly section: it measures the
        # contigs the assembler produced, not the alignment and not
        # the classifier annotations downstream of those contigs.
        assembly_section = self._build_section(
            "Assembly statistics",
            self.sections["assembly"].generate_section,
            quast_reports=quast_paths,
        )

        contig_classification_section = self._build_section(
            "Assembly classification",
            self.sections["contig_classification"].generate_section,
            blastn_files=blastn_paths,
            genomad_summaries=genomad_paths,
        )

        coverage_section = self._build_section(
            "Alignment coverage",
            self.sections["coverage"].generate_section,
            mosdepth_regions=mosdepth_regions,
            virus_names=virus_names,
        )

        try:
            header = self._create_main_header(sample_name)
            main_tabs = pn.Tabs(
                ("Dashboard", dashboard_section),
                ("Read statistics", read_statistics_section),
                ("Host alignment", host_alignment_section),
                ("Classification of reads", raw_classification_section),
                ("Assembly statistics", assembly_section),
                ("Assembly classification", contig_classification_section),
                ("Alignment coverage", coverage_section),
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
        for x in plural or []:
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

    def _logo_data_uri(self) -> str:
        """Return the bundled reportHanter wordmark as a base64 data
        URI, or an empty string when the asset cannot be loaded.

        The PNG is shipped inside the ``reporthanter.assets`` package
        (declared in ``pyproject.toml`` ``package-data``) and embedded
        directly into the rendered HTML so the saved report has no
        external network dependency.
        """
        try:
            with (
                resources.files("reporthanter.assets")
                .joinpath("reporthanter_logo.png")
                .open("rb")
            ) as fh:
                data = base64.b64encode(fh.read()).decode("ascii")
            return f"data:image/png;base64,{data}"
        except Exception as exc:  # noqa: BLE001
            self.logger.warning(f"Could not load reportHanter logo: {exc}")
            return ""

    def _create_main_header(self, sample_name: str) -> pn.pane.HTML:
        """Render the top-of-report banner.

        White background, navy + teal brand palette, the
        reportHanter wordmark on the left and the sample name set
        large on the right. The ``ReportHanter Report`` title text
        is dropped because the wordmark already carries it; the
        sample name is now the only piece of information the
        reviewer needs to see at a glance.
        """
        primary = self.config.get("report.primary_color", "#102D5F")
        accent = self.config.get("report.accent_color", "#13B5A6")
        background = self.config.get("report.header_bg_color", "#ffffff")
        logo_uri = self._logo_data_uri()
        if logo_uri:
            logo_html = (
                f'<img src="{logo_uri}" alt="reportHanter" '
                'style="height:64px;display:block">'
            )
        else:
            logo_html = (
                f'<span style="font-size:22px;color:{primary};'
                f'font-weight:700;letter-spacing:0.02em">reportHanter</span>'
            )
        return pn.pane.HTML(
            f"""
            <div style="display:flex;align-items:center;
                        justify-content:space-between;
                        padding:18px 28px;background:{background};
                        border-bottom:3px solid {accent};
                        margin:10px;border-radius:4px;
                        box-shadow:0 1px 2px rgba(0,0,0,0.04)">
              <div>{logo_html}</div>
              <div style="text-align:right">
                <div style="font-size:11px;color:#5a6478;
                            letter-spacing:0.10em;
                            text-transform:uppercase;
                            margin-bottom:4px">Sample</div>
                <div style="font-size:26px;color:{primary};
                            font-weight:700;line-height:1.1">
                  {sample_name}
                </div>
              </div>
            </div>
            """,
            sizing_mode="stretch_width",
        )

    def save_report(
        self, report: pn.Column, output_path: str | Path, title: str | None = None
    ) -> None:
        """Save the report to an HTML file."""
        try:
            title = title or "reportHanter"
            report.save(str(output_path), title=title)
            self.logger.info(f"Report saved to: {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to save report to {output_path}: {e}")
            raise ReportGenerationError(f"Failed to save report: {e}") from e
