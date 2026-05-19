"""
Report sections with improved separation of concerns.
"""

import logging
from pathlib import Path

import pandas as pd
import panel as pn

from ..core.config import DefaultConfig
from ..core.interfaces import ReportSection
from ..processors.blast_processor import BlastPlotGenerator, BlastProcessor
from ..processors.coverage_processor import CoveragePlotGenerator, CoverageProcessor
from ..processors.fastp_processor import FastpProcessor
from ..processors.flagstat_processor import FlagstatProcessor
from ..processors.kaiju_processor import KaijuPlotGenerator, KaijuProcessor
from ..processors.kraken_processor import KrakenPlotGenerator, KrakenProcessor


class _SectionBase(ReportSection):
    """Shared scaffolding for report sections: config, logger, header helper."""

    def __init__(self, config: DefaultConfig | None = None):
        self.config = config or DefaultConfig()
        self.logger = logging.getLogger(self.__class__.__name__)

    def _create_header(self, text: str, height: int = 150) -> pn.pane.Markdown:
        """Create a styled header for the section."""
        return pn.pane.Markdown(
            text,
            styles={
                "color": "white",
                "padding": "10px",
                "text-align": "left",
                "font-size": "16px",
                "background": self.config.get("report.header_color", "#04c273"),
                "margin": "10px",
                "height": f"{height}px",
            },
        )

    def _filters_block(self, lines: list[str]) -> pn.pane.Markdown:
        """Small read-only block listing the active filter thresholds.

        Rendered below the section header so the reader knows which
        cutoffs produced the plots without having to rerun the pipeline.
        """
        body = "\n".join(f"- {line}" for line in lines)
        return pn.pane.Markdown(
            f"**Filters applied**\n\n{body}",
            styles={
                "font-size": "12px",
                "padding": "4px 12px",
                "margin": "0 10px 10px 10px",
                "color": "#333",
                "background": "#f3f3f3",
                "border-left": "3px solid #04c273",
            },
        )


class AlignmentStatsSection(_SectionBase):
    """Report section for alignment statistics and read quality."""

    @property
    def section_name(self) -> str:
        return "Alignment and Read Statistics"

    def generate_section(self, **kwargs) -> pn.Column:
        """Generate alignment statistics section."""
        flagstat_file = kwargs.get("flagstat_file")
        fastp_json = kwargs.get("fastp_json")
        secondary_flagstat_file = kwargs.get("secondary_flagstat_file")
        secondary_host = kwargs.get("secondary_host", "Secondary")

        if not flagstat_file or not fastp_json:
            raise ValueError("flagstat_file and fastp_json are required")

        # Process alignment stats
        flagstat_processor = FlagstatProcessor(self.config.get_config("flagstat"))
        flagstat_data = flagstat_processor.process(flagstat_file)
        human_stats, human_pane = flagstat_processor.create_alignment_stats(flagstat_data, "Human")

        # Process secondary alignment if provided
        secondary_components = []
        if secondary_flagstat_file:
            secondary_data = flagstat_processor.process(secondary_flagstat_file)
            secondary_stats, secondary_pane = flagstat_processor.create_alignment_stats(
                secondary_data, secondary_host
            )
            secondary_components = [secondary_stats, pn.layout.Divider(), secondary_pane]

        # Process FastP data
        fastp_processor = FastpProcessor(self.config.get_config("fastp"))
        fastp_data = fastp_processor.process(fastp_json)
        fastp_table = fastp_processor.create_summary_table(fastp_data)

        header = self._create_header(
            """
            ## Alignment and Read Statistics
            Reads were aligned to Human and optionally other host species with bwa.
            """,
            height=80,
        )

        alignment_components = [
            human_stats,
            pn.layout.Divider(),
            human_pane,
        ]
        alignment_components.extend(secondary_components)

        flagstat_column = pn.Column(*alignment_components, name="Alignment")
        tabs = pn.Tabs(flagstat_column, fastp_table)

        return pn.Column(header, tabs)


class RawClassificationSection(_SectionBase):
    """Report section for raw read classification (Kraken and Kaiju)."""

    @property
    def section_name(self) -> str:
        return "Classification of Raw Reads"

    def generate_section(self, **kwargs) -> pn.Column:
        """Generate raw classification section."""
        kraken_file = kwargs.get("kraken_file")
        kaiju_table = kwargs.get("kaiju_table")

        if not kraken_file or not kaiju_table:
            raise ValueError("kraken_file and kaiju_table are required")

        # Process Kraken data
        kraken_processor = KrakenProcessor(self.config.get_config("kraken"))
        kraken_plot_generator = KrakenPlotGenerator(self.config.get_config("plotting"))

        kraken_data = kraken_processor.process(kraken_file)

        # Create virus-only plot
        kraken_config = self.config.get_config("filtering.kraken")
        virus_data, virus_unclassified = kraken_processor.filter_data(
            kraken_data, virus_only=True, **kraken_config
        )
        virus_plot = kraken_plot_generator.generate_plot(
            virus_data,
            title="Kraken Virus Classification",
            unclassified_pct=virus_unclassified,
        ).interactive()

        # Create domain plot
        domain_data, domain_unclassified = kraken_processor.filter_data(
            kraken_data, level="domain", virus_only=False, **kraken_config
        )
        domain_plot = kraken_plot_generator.generate_plot(
            domain_data,
            title="Kraken Domain Classification",
            unclassified_pct=domain_unclassified,
        ).interactive()

        # Process Kaiju data
        kaiju_processor = KaijuProcessor(self.config.get_config("kaiju"))
        kaiju_plot_generator = KaijuPlotGenerator(self.config.get_config("plotting"))

        kaiju_data = kaiju_processor.process(kaiju_table)
        kaiju_config = self.config.get_config("filtering.kaiju")
        kaiju_filtered, kaiju_unclassified = kaiju_processor.filter_data(kaiju_data, **kaiju_config)

        kaiju_plot = kaiju_plot_generator.generate_plot(
            kaiju_filtered,
            title="Kaiju Classification",
            unclassified_pct=kaiju_unclassified,
        ).interactive()

        header = self._create_header(
            """
            ## Classification of Raw Reads
            Reads were classified with Kraken2 and Kaiju.
            """,
            height=80,
        )

        filters = self._filters_block(
            [
                f"Kraken level: {kraken_config.get('level', 'species')}",
                f"Kraken cutoff: {kraken_config.get('cutoff', 0.001)} (fraction of total reads)",
                f"Kraken max entries: {kraken_config.get('max_entries', 10)}",
                f"Kraken virus-only filter: {kraken_config.get('virus_only', True)}",
                f"Kaiju cutoff: {kaiju_config.get('cutoff', 0.01)}",
                f"Kaiju max entries: {kaiju_config.get('max_entries', 10)}",
            ]
        )

        kraken_virus_pane = pn.pane.Vega(
            virus_plot, sizing_mode="stretch_both", name="Kraken Virus Only"
        )
        kraken_domain_pane = pn.pane.Vega(
            domain_plot, sizing_mode="stretch_both", name="Kraken All Domains"
        )
        kaiju_pane = pn.pane.Vega(kaiju_plot, sizing_mode="stretch_both", name="Kaiju")

        tabs = pn.Tabs(kraken_virus_pane, kraken_domain_pane, kaiju_pane)

        return pn.Column(header, filters, tabs)


class ContigClassificationSection(_SectionBase):
    """Report section for contig classification (BLAST)."""

    @property
    def section_name(self) -> str:
        return "Classification of Contigs"

    def generate_section(self, **kwargs) -> pn.Column:
        """Generate contig classification section."""
        blastn_file = kwargs.get("blastn_file")

        if not blastn_file:
            raise ValueError("blastn_file is required")

        # Process BLAST data
        blast_processor = BlastProcessor(self.config.get_config("blast"))
        blast_plot_generator = BlastPlotGenerator(self.config.get_config("plotting"))

        blast_data = blast_processor.process(blastn_file)
        blast_plot = blast_plot_generator.generate_plot(blast_data).interactive()

        # Create table for contig data
        table_data = blast_data.copy()
        if table_data.empty:
            table_data = pd.DataFrame({"sequence": ["NO SEQUENCES GENERATED"]})
        else:
            # Clean up table data
            columns_to_drop = ["name", "matches"]
            table_data = table_data.drop(
                columns=[col for col in columns_to_drop if col in table_data.columns]
            )

        # Tabulator copy button for the sequence column. Tabulator's
        # built-in row-menu copy works for whole rows; a column formatter
        # gives a per-cell copy that lands the sequence on the clipboard
        # without selecting the cell first.
        formatters: dict = {}
        if "sequence" in table_data.columns:
            formatters["sequence"] = {
                "type": "textarea",
            }

        blast_table = pn.widgets.Tabulator(
            table_data,
            formatters=formatters,
            layout="fit_columns",
            pagination="local",
            page_size=15,
            show_index=False,
            configuration={
                "clipboard": True,
                "clipboardCopyRowRange": "active",
                "clipboardCopyConfig": {
                    "columnHeaders": True,
                    "rowGroups": False,
                    "columnCalcs": False,
                },
            },
            name="Contig Table",
        )

        # CSV download button — Tabulator exposes a .download() JS method
        # we trigger from a Panel button via the widget's API.
        download_button = pn.widgets.Button(
            name="Download contig table as CSV",
            button_type="default",
            margin=(5, 10),
        )

        def _download(event):
            blast_table.download("contig_table.csv")

        download_button.on_click(_download)

        header = self._create_header(
            """
            ## Classification of Contigs
            Contigs generated by MEGAHIT were classified using BLASTN.
            Select rows and press Ctrl/Cmd-C to copy, or use the
            download button below to export the full table as CSV.
            """,
            height=120,
        )

        filters = self._filters_block(
            [
                f"BLAST cutoff: {self.config.get('filtering.blast.cutoff', 'n/a')}",
                f"BLAST max entries: {self.config.get('filtering.blast.max_entries', 'n/a')}",
            ]
        )

        blast_pane = pn.pane.Vega(blast_plot, sizing_mode="stretch_both", name="BLASTN")
        tabs = pn.Tabs(blast_pane, blast_table)

        return pn.Column(header, filters, tabs, download_button)


class CoverageSection(_SectionBase):
    """Report section for alignment coverage plots."""

    @property
    def section_name(self) -> str:
        return "Alignment Coverage"

    def generate_section(self, **kwargs) -> pn.Column:
        """Generate coverage plots section.

        Prefers an interactive Altair trace built from a mosdepth
        regions BED when ``mosdepth_regions`` is supplied. Falls back to
        the legacy SVG embedding when only ``coverage_folder`` is
        available so older callers keep working unchanged.
        """
        coverage_folder = kwargs.get("coverage_folder")
        mosdepth_regions = kwargs.get("mosdepth_regions")

        if not coverage_folder and not mosdepth_regions:
            raise ValueError("coverage_folder or mosdepth_regions is required")

        header = self._create_header("## Alignment Coverage", height=80)
        tabs = pn.Tabs()

        rendered = False
        if mosdepth_regions:
            rendered = self._append_interactive_tabs(tabs, mosdepth_regions)

        if not rendered and coverage_folder:
            rendered = self._append_svg_tabs(tabs, Path(coverage_folder))

        if not rendered:
            tabs.append(
                pn.pane.Markdown("## No Coverage Plots Available", name="No Coverage Plots")
            )
            self.logger.warning("No coverage data available")

        return pn.Column(header, tabs)

    def _append_interactive_tabs(self, tabs: pn.Tabs, regions_path: str | Path) -> bool:
        """Render one Altair tab per reference; return True if anything added."""
        processor = CoverageProcessor(self.config.get_config("coverage"))
        plot_generator = CoveragePlotGenerator(self.config.get_config("plotting"))

        try:
            df = processor.process(regions_path)
        except Exception as e:
            self.logger.warning(f"Could not read mosdepth regions {regions_path}: {e}")
            return False

        if df.empty:
            self.logger.warning(f"Mosdepth regions file is empty: {regions_path}")
            return False

        for chrom, sub in df.groupby("chrom", sort=True):
            chart = plot_generator.generate_plot(sub, chrom=str(chrom)).interactive()
            tabs.append(pn.pane.Vega(chart, sizing_mode="stretch_both", name=str(chrom)))

        self.logger.info(
            f"Added {df['chrom'].nunique()} interactive coverage plots from {regions_path}"
        )
        return True

    def _append_svg_tabs(self, tabs: pn.Tabs, coverage_path: Path) -> bool:
        """Legacy path: embed bam2plot SVGs. Returns True if anything added."""
        if not coverage_path.exists() or not coverage_path.is_dir():
            self.logger.warning(f"Coverage folder missing: {coverage_path}")
            return False

        coverage_plots = sorted(
            x for x in coverage_path.iterdir() if x.suffix == ".svg" and not x.name.startswith("._")
        )
        if not coverage_plots:
            return False

        for plot_file in coverage_plots:
            tabs.append(pn.pane.SVG(plot_file, sizing_mode="stretch_width", name=plot_file.stem))
        self.logger.info(f"Added {len(coverage_plots)} coverage plots to report")
        return True
