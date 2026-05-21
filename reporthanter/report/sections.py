"""
Report sections with improved separation of concerns.
"""

import logging

import pandas as pd
import panel as pn

from ..core.config import DefaultConfig
from ..core.interfaces import ReportSection
from ..processors.blast_processor import BlastPlotGenerator, BlastProcessor
from ..processors.coverage_processor import CoveragePlotGenerator, CoverageProcessor
from ..processors.fastp_processor import FastpProcessor
from ..processors.flagstat_processor import FlagstatProcessor
from ..processors.genomad_processor import GenomadProcessor
from ..processors.kaiju_processor import KaijuPlotGenerator, KaijuProcessor
from ..processors.kraken_processor import KrakenPlotGenerator, KrakenProcessor
from ..processors.quast_processor import QuastProcessor


class _SectionBase(ReportSection):
    """Shared scaffolding for report sections: config, logger, header helper."""

    def __init__(self, config: DefaultConfig | None = None):
        self.config = config or DefaultConfig()
        self.logger = logging.getLogger(self.__class__.__name__)

    def _create_header(self, text: str) -> pn.pane.Markdown:
        """Create a styled header for the section.

        The pane sizes to its Markdown content; an earlier fixed pixel
        height clipped multi-line subtitles on the Alignment and Raw
        Classification sections.
        """
        return pn.pane.Markdown(
            text,
            styles={
                "color": "white",
                "padding": "10px 15px",
                "text-align": "left",
                "font-size": "16px",
                "background": self.config.get("report.header_color", "#04c273"),
                "margin": "10px",
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
                "border-left": "3px solid #067a48",
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
        quast_reports = kwargs.get("quast_reports")
        if not quast_reports and kwargs.get("quast_report"):
            quast_reports = [kwargs["quast_report"]]

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
            """
        )

        alignment_components = [
            human_stats,
            pn.layout.Divider(),
            human_pane,
        ]
        alignment_components.extend(secondary_components)

        flagstat_column = pn.Column(*alignment_components, name="Alignment")
        tab_panes: list = [flagstat_column, fastp_table]

        # Optional QUAST assembly summary, supplied by virusHanter2 when
        # the QUAST flag is on. One sub-tab per (sample, assembler).
        if quast_reports:
            for qpath in quast_reports:
                try:
                    quast_processor = QuastProcessor(self.config.get_config("quast"))
                    quast_data = quast_processor.process(qpath)
                    tab_panes.append(quast_processor.create_summary_table(quast_data))
                except Exception as e:  # noqa: BLE001
                    self.logger.warning(f"Could not render QUAST report {qpath}: {e}")

        tabs = pn.Tabs(*tab_panes)
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
        )

        # Create domain plot
        domain_data, domain_unclassified = kraken_processor.filter_data(
            kraken_data, level="domain", virus_only=False, **kraken_config
        )
        domain_plot = kraken_plot_generator.generate_plot(
            domain_data,
            title="Kraken Domain Classification",
            unclassified_pct=domain_unclassified,
        )

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
        )

        header = self._create_header(
            """
            ## Classification of Raw Reads
            Reads were classified with Kraken2 and Kaiju.
            """
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
        """Generate contig classification section.

        Accepts a list of BLAST merged CSVs (one per assembler).
        Each CSV is expected to carry an ``assembler`` column written
        upstream by virusHanter2's ``wrangle_pilon`` rule. Rows
        without the column are tagged ``unknown`` so the column is
        always present in the rendered table.
        """
        blastn_files = kwargs.get("blastn_files")
        # Backwards compatibility: tolerate a singular ``blastn_file``
        # for callers that still pass the legacy parameter name.
        if not blastn_files and kwargs.get("blastn_file"):
            blastn_files = [kwargs["blastn_file"]]
        genomad_summaries = kwargs.get("genomad_summaries")
        if not genomad_summaries and kwargs.get("genomad_summary"):
            genomad_summaries = [kwargs["genomad_summary"]]

        if not blastn_files:
            raise ValueError("blastn_files is required")

        # Process BLAST data — concatenate one frame per assembler so
        # the contig table and the headline bar chart carry the union
        # of contigs with their assembler tag.
        blast_processor = BlastProcessor(self.config.get_config("blast"))
        blast_plot_generator = BlastPlotGenerator(self.config.get_config("plotting"))

        per_assembler_frames: list[pd.DataFrame] = []
        for path in blastn_files:
            try:
                frame = blast_processor.process(path)
            except Exception as e:  # noqa: BLE001
                self.logger.warning(f"Could not parse BLAST CSV {path}: {e}")
                continue
            if frame is None or frame.empty:
                continue
            if "assembler" not in frame.columns:
                frame = frame.assign(assembler="unknown")
            per_assembler_frames.append(frame)
        blast_data = (
            pd.concat(per_assembler_frames, ignore_index=True)
            if per_assembler_frames
            else pd.DataFrame()
        )

        blast_plot = blast_plot_generator.generate_plot(blast_data)

        # Create table for contig data
        table_data = blast_data.copy()
        if table_data.empty:
            table_data = pd.DataFrame({"sequence": ["NO SEQUENCES GENERATED"]})
        else:
            # Clean up table data. sample_id is the same value on every
            # row of a single-sample report and is already shown in the
            # main banner, so drop it. Keep `assembler` and move it to
            # the second position so reviewers can see which assembler
            # produced each row without horizontal scrolling.
            columns_to_drop = ["name", "matches", "sample_id"]
            table_data = table_data.drop(
                columns=[col for col in columns_to_drop if col in table_data.columns]
            )
            if "assembler" in table_data.columns:
                cols = ["assembler"] + [
                    c for c in table_data.columns if c != "assembler"
                ]
                table_data = table_data[cols]

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

        # Per-assembler headline counts for the section intro. Helps
        # the reviewer see at a glance whether MEGAHIT and metaSPAdes
        # produced comparable numbers of classified contigs before
        # diving into the per-row table.
        if "assembler" in blast_data.columns and not blast_data.empty:
            counts = blast_data["assembler"].value_counts().sort_index()
            counts_md = ", ".join(f"{asm}: {n}" for asm, n in counts.items())
            counts_line = f"Classified contigs by assembler: {counts_md}."
        else:
            counts_line = ""

        header = self._create_header(
            f"""
            ## Classification of Contigs
            Contigs were classified using BLASTN. {counts_line}
            Select rows and press Ctrl/Cmd-C to copy, or use the
            download button below to export the full table as CSV.
            """
        )

        # No per-report BLAST filtering is applied here: the input CSV
        # is already pre-filtered upstream (BLASTN + CheckV merge in
        # virusHanter2), so a "Filters applied" block on this section
        # would only repeat upstream defaults.

        blast_pane = pn.pane.Vega(blast_plot, sizing_mode="stretch_both", name="BLASTN")
        tab_panes: list = [blast_pane, blast_table]

        # Optional geNomad call-tables — one sub-tab per assembler
        # when virusHanter2 ran geNomad alongside CheckV.
        if genomad_summaries:
            for gpath in genomad_summaries:
                try:
                    gp = GenomadProcessor(self.config.get_config("genomad"))
                    gdf = gp.process(gpath)
                    tab_panes.append(gp.create_summary_table(gdf))
                except Exception as e:  # noqa: BLE001
                    self.logger.warning(
                        f"Could not render geNomad summary {gpath}: {e}"
                    )

        tabs = pn.Tabs(*tab_panes)
        return pn.Column(header, tabs, download_button)


class CoverageSection(_SectionBase):
    """Report section for alignment coverage plots."""

    @property
    def section_name(self) -> str:
        return "Alignment Coverage"

    def generate_section(self, **kwargs) -> pn.Column:
        """Generate coverage plots section.

        Renders one interactive Altair trace per reference from the
        mosdepth ``regions.bed.gz`` produced upstream. If a
        ``virus_names`` TSV is supplied (a sidecar emitted by
        virusHanter2's ``bwa_align_to_kraken_hits`` rule), tab labels
        carry both the chrom (accession) and the friendly species
        name as ``<chrom> -- <name>``.
        """
        mosdepth_regions = kwargs.get("mosdepth_regions")
        virus_names = kwargs.get("virus_names")
        if not mosdepth_regions:
            raise ValueError("mosdepth_regions is required")

        header = self._create_header("## Alignment Coverage")
        tabs = pn.Tabs()

        processor = CoverageProcessor(self.config.get_config("coverage"))
        plot_generator = CoveragePlotGenerator(self.config.get_config("plotting"))

        try:
            df = processor.process(mosdepth_regions)
        except Exception as e:  # noqa: BLE001
            self.logger.warning(f"Could not read mosdepth regions {mosdepth_regions}: {e}")
            df = pd.DataFrame()

        if df.empty:
            tabs.append(
                pn.pane.Markdown("## No Coverage Plots Available", name="No Coverage Plots")
            )
            self.logger.warning(f"Mosdepth regions file empty or unreadable: {mosdepth_regions}")
            return pn.Column(header, tabs)

        chrom_to_name: dict[str, str] = {}
        if virus_names:
            try:
                names_df = pd.read_csv(virus_names, sep="\t")
                if {"chrom", "name"}.issubset(names_df.columns):
                    chrom_to_name = dict(
                        zip(
                            names_df["chrom"].astype(str),
                            names_df["name"].fillna("").astype(str),
                            strict=False,
                        )
                    )
            except Exception as e:  # noqa: BLE001
                self.logger.warning(f"Could not read virus-names sidecar {virus_names}: {e}")

        for chrom, sub in df.groupby("chrom", sort=True):
            chart = plot_generator.generate_plot(sub, chrom=str(chrom)).interactive()
            species = chrom_to_name.get(str(chrom), "")
            label = f"{chrom} — {species}" if species else str(chrom)
            tabs.append(pn.pane.Vega(chart, sizing_mode="stretch_both", name=label))

        self.logger.info(
            f"Added {df['chrom'].nunique()} interactive coverage plots from {mosdepth_regions}"
        )
        return pn.Column(header, tabs)
