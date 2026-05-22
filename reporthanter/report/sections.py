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


def _coverage_stats_table(
    sub: pd.DataFrame, thresholds: list[int]
) -> pn.widgets.Tabulator:
    """Per-reference coverage statistics rendered below the trace.

    ``sub`` is the slice of the mosdepth regions BED for one
    ``chrom``: rows are windowed entries with columns
    ``chrom, start, end, depth, mid``. The Tabulator below the
    coverage trace shows reference length, total mapped bases,
    mean depth, and bp / % at each requested depth threshold.

    The "bp >= T" counts are an approximation in
    ``COVERAGE_WINDOW``-sized chunks: every window whose mean
    depth is at least ``T`` contributes ``end - start`` bp. The
    approximation is tight enough at the 50-100 bp window sizes
    the pipeline uses; for exact per-base counts, mosdepth's
    own ``.thresholds.bed.gz`` is the source of truth and could
    be plumbed in later.
    """
    if sub.empty or "depth" not in sub.columns:
        return pn.widgets.Tabulator(
            pd.DataFrame({"Metric": ["Reference length"], "Value": ["unknown"]}),
            disabled=True,
            show_index=False,
            layout="fit_columns",
            pagination=None,
        )

    window_len = (sub["end"] - sub["start"]).astype(int)
    ref_length = int(window_len.sum())
    total_bases = float((sub["depth"] * window_len).sum())
    mean_depth = total_bases / ref_length if ref_length else 0.0

    rows: list[dict[str, str]] = [
        {"Metric": "Reference length (bp)", "Value": f"{ref_length:,}"},
        {"Metric": "Mean depth", "Value": f"{mean_depth:.2f}"},
        {"Metric": "Median depth", "Value": f"{float(sub['depth'].median()):.2f}"},
        {"Metric": "Max depth", "Value": f"{int(sub['depth'].max())}"},
    ]
    for threshold in thresholds:
        passing = window_len[sub["depth"] >= threshold].sum()
        passing_bp = int(passing)
        pct = (100.0 * passing_bp / ref_length) if ref_length else 0.0
        rows.append(
            {
                "Metric": f"bp >= {threshold}x",
                "Value": f"{passing_bp:,} ({pct:.1f}%)",
            }
        )

    return pn.widgets.Tabulator(
        pd.DataFrame(rows),
        disabled=True,
        show_index=False,
        layout="fit_columns",
        pagination=None,
    )


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


class ReadStatisticsSection(_SectionBase):
    """Report section for raw read quality (fastp summary).

    Splits the former combined "Alignment and Read Statistics"
    panel: this section carries the fastp summary alone so it
    reads as a pure read-QC story, with host alignment moved into
    its own sibling section.
    """

    @property
    def section_name(self) -> str:
        return "Read statistics"

    def generate_section(self, **kwargs) -> pn.Column:
        fastp_json = kwargs.get("fastp_json")
        if not fastp_json:
            raise ValueError("fastp_json is required")

        fastp_processor = FastpProcessor(self.config.get_config("fastp"))
        fastp_data = fastp_processor.process(fastp_json)
        fastp_table = fastp_processor.create_summary_table(fastp_data)

        header = self._create_header(
            """
            ## Read statistics
            Read-level quality from fastp: number of reads, length,
            Q20/Q30 rates, duplication rate, GC content. These
            describe the input before host removal and assembly.
            """
        )
        return pn.Column(header, fastp_table)


class HostAlignmentSection(_SectionBase):
    """Report section for host alignment outcome (samtools flagstat).

    The flagstat shows how many reads landed on the host
    reference (and on the optional secondary host) and therefore
    did *not* feed the downstream classifiers and assemblers. The
    `host_removal_tool` column in the per-batch run-info CSV
    records whether the pre-processing used `bwa` or `hostile`.
    """

    @property
    def section_name(self) -> str:
        return "Host alignment"

    def generate_section(self, **kwargs) -> pn.Column:
        flagstat_file = kwargs.get("flagstat_file")
        secondary_flagstat_file = kwargs.get("secondary_flagstat_file")
        secondary_host = kwargs.get("secondary_host", "Secondary")
        if not flagstat_file:
            raise ValueError("flagstat_file is required")

        flagstat_processor = FlagstatProcessor(self.config.get_config("flagstat"))
        flagstat_data = flagstat_processor.process(flagstat_file)
        human_stats, human_pane = flagstat_processor.create_alignment_stats(
            flagstat_data, "Human"
        )

        components = [human_stats, pn.layout.Divider(), human_pane]
        if secondary_flagstat_file:
            secondary_data = flagstat_processor.process(secondary_flagstat_file)
            secondary_stats, secondary_pane = (
                flagstat_processor.create_alignment_stats(
                    secondary_data, secondary_host
                )
            )
            components.extend(
                [pn.layout.Divider(), secondary_stats, pn.layout.Divider(),
                 secondary_pane]
            )

        header = self._create_header(
            """
            ## Host alignment
            Read pairs aligned to the host reference (typically
            human; optionally a second host like mouse) and removed
            before classification and assembly. Counts come from
            samtools flagstat.
            """
        )
        return pn.Column(header, *components)


class RawClassificationSection(_SectionBase):
    """Report section for raw read classification (Kraken and Kaiju)."""

    @property
    def section_name(self) -> str:
        return "Classification of reads"

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
            ## Classification of reads
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


class AssemblySection(_SectionBase):
    """Report section for de novo assembly metrics (QUAST per assembler).

    QUAST measures the contigs produced by the de novo assembler
    before any viral classification or contamination check. Each
    active assembler in ``virusHanter2``'s ``config[ASSEMBLERS]``
    contributes one ``report.tsv``; this section renders one
    sub-tab per assembler showing N50, the number of contigs, the
    largest contig, GC content and the standard QUAST metric set.
    """

    @property
    def section_name(self) -> str:
        return "Assembly statistics"

    def generate_section(self, **kwargs) -> pn.Column:
        """Generate the assembly section.

        Accepts a list of QUAST ``report.tsv`` paths via
        ``quast_reports`` (one per assembler). The plural form
        mirrors the multi-assembler shape used by the other
        sections; a singular ``quast_report`` is still accepted
        for legacy single-assembler callers.
        """
        quast_reports = kwargs.get("quast_reports")
        if not quast_reports and kwargs.get("quast_report"):
            quast_reports = [kwargs["quast_report"]]

        header = self._create_header(
            """
            ## Assembly
            Assembly metrics from QUAST, one sub-tab per
            assembler. Numbers refer to the polished contigs the
            assembler produced before BLAST classification or
            CheckV contamination assessment.
            """
        )

        if not quast_reports:
            return pn.Column(
                header,
                pn.pane.Markdown(
                    "*No QUAST reports were supplied. Enable "
                    "`QUAST: \"TRUE\"` in the virusHanter2 config "
                    "to populate this section.*"
                ),
            )

        tab_panes: list = []
        for qpath in quast_reports:
            try:
                quast_processor = QuastProcessor(
                    self.config.get_config("quast")
                )
                quast_data = quast_processor.process(qpath)
                # Derive the assembler label from the report path:
                # virusHanter2 writes
                # ``{sample}/{assembler}/QUAST/report.tsv``, so the
                # third-from-last path component is the assembler
                # name. Fall back to "Assembly (QUAST)" on
                # unexpected paths so the widget still has a label.
                from pathlib import Path as _P
                parts = _P(str(qpath)).parts
                label = parts[-3] if len(parts) >= 3 else "Assembly (QUAST)"
                tab_panes.append(
                    quast_processor.create_summary_table(
                        quast_data, name=label
                    )
                )
            except Exception as e:  # noqa: BLE001
                self.logger.warning(
                    f"Could not render QUAST report {qpath}: {e}"
                )

        if not tab_panes:
            return pn.Column(
                header,
                pn.pane.Markdown(
                    "*QUAST reports were supplied but could not "
                    "be parsed; see the run log.*"
                ),
            )

        return pn.Column(header, pn.Tabs(*tab_panes))


class ContigClassificationSection(_SectionBase):
    """Report section for contig classification (BLAST)."""

    @property
    def section_name(self) -> str:
        return "Assembly classification"

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

        def _table_view(frame: pd.DataFrame) -> pd.DataFrame:
            """Drop bookkeeping columns and pin ``assembler`` first.

            Kept as a closure so the assembler-filter callback can
            project the filtered BLAST frame through exactly the same
            column shape as the initial render.
            """
            if frame.empty:
                return pd.DataFrame({"sequence": ["NO SEQUENCES GENERATED"]})
            columns_to_drop = ["name", "matches", "sample_id"]
            view = frame.drop(
                columns=[col for col in columns_to_drop if col in frame.columns]
            )
            if "assembler" in view.columns:
                cols = ["assembler"] + [c for c in view.columns if c != "assembler"]
                view = view[cols]
            return view

        blast_plot = blast_plot_generator.generate_plot(blast_data)
        table_data = _table_view(blast_data)
        present_assemblers: list[str] = (
            sorted(blast_data["assembler"].dropna().unique().astype(str).tolist())
            if ("assembler" in blast_data.columns and not blast_data.empty)
            else []
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
            name=(
                "All assemblers"
                if (
                    "assembler" in blast_data.columns
                    and not blast_data.empty
                    and blast_data["assembler"].nunique() > 1
                )
                else "Contig Table"
            ),
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
            Contigs from de novo assembly are classified with
            BLASTN. {counts_line} When geNomad is enabled in the
            pipeline, a per-assembler geNomad summary sub-tab is
            added. Select rows and press Ctrl/Cmd-C to copy, or
            use the download button below to export the full
            table as CSV.
            """
        )

        # No per-report BLAST filtering is applied here: the input CSV
        # is already pre-filtered upstream (BLASTN + CheckV merge in
        # virusHanter2), so a "Filters applied" block on this section
        # would only repeat upstream defaults.

        # Multi-assembler reports: one sub-tab per assembler plus an
        # "All assemblers" union tab; each tab carries its own BLAST
        # bar chart on top and the matching contig table below. The
        # tab-switch is baked into the static HTML so the saved file
        # is fully interactive without a Panel server. (Panel's
        # `param.watch` callbacks only fire under a live server.)
        #
        # Single-assembler runs keep the original two-tab shape
        # (BLAST chart, contig table).
        def _build_assembler_tab(name: str, frame: pd.DataFrame) -> pn.Column:
            count_plot = blast_plot_generator.generate_plot(frame)
            # Cumulative-bp companion chart: sums contig lengths
            # per BLAST match so reviewers see the assembled span
            # per reference, not just the contig count.
            bp_plot = blast_plot_generator.create_bp_chart(frame)
            sub_table = pn.widgets.Tabulator(
                _table_view(frame),
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
            )
            # Fix each Vega pane to stretch_width with a bounded
            # height. Without the height bound, `stretch_both` lets
            # the chart container expand to fill its parent and
            # overlap whatever sits below it in the saved HTML.
            return pn.Column(
                pn.pane.Vega(
                    count_plot,
                    sizing_mode="stretch_width",
                    height=420,
                ),
                pn.pane.Vega(
                    bp_plot,
                    sizing_mode="stretch_width",
                    height=420,
                ),
                sub_table,
                name=name,
                sizing_mode="stretch_width",
            )

        if len(present_assemblers) > 1:
            tab_panes: list = [_build_assembler_tab("All assemblers", blast_data)]
            for asm in present_assemblers:
                tab_panes.append(
                    _build_assembler_tab(
                        asm, blast_data.loc[blast_data["assembler"] == asm]
                    )
                )
        else:
            blast_pane = pn.pane.Vega(
                blast_plot, sizing_mode="stretch_both", name="BLASTN"
            )
            tab_panes = [blast_pane, blast_table]

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
        return "Alignment coverage"

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

        header = self._create_header("## Alignment coverage")
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
        chrom_to_sources: dict[str, str] = {}
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
                # Optional `sources` column added when virusHanter2
                # builds the reference set from the union of
                # classifier outputs. Older sidecars do not have it;
                # the tab label then falls back to the original
                # ``<chrom> — <species>`` shape.
                if "sources" in names_df.columns:
                    chrom_to_sources = dict(
                        zip(
                            names_df["chrom"].astype(str),
                            names_df["sources"].fillna("").astype(str),
                            strict=False,
                        )
                    )
            except Exception as e:  # noqa: BLE001
                self.logger.warning(f"Could not read virus-names sidecar {virus_names}: {e}")

        # Coverage thresholds reported beneath each trace. 1x is the
        # parity-locked "any coverage" floor; 3x / 5x / 10x are the
        # standard clinical depth ladders for consensus quality;
        # 100x is included for high-coverage references where the
        # reviewer wants to see how much of the reference was
        # deeply oversampled.
        thresholds = [1, 3, 5, 10, 100]

        for chrom, sub in df.groupby("chrom", sort=True):
            chart = plot_generator.generate_plot(sub, chrom=str(chrom)).interactive()
            species = chrom_to_name.get(str(chrom), "")
            sources = chrom_to_sources.get(str(chrom), "")
            base = f"{chrom} — {species}" if species else str(chrom)
            label = f"{base} [{sources}]" if sources else base

            # Per-reference statistics table. mosdepth's regions BED
            # carries depth per window of size COVERAGE_WINDOW; we
            # approximate "bp at depth >= T" as
            # sum(window_length where depth >= T). At small window
            # sizes (50-100 bp) the approximation is tight enough
            # for the depth ladders typical of viral metagenomics.
            stats_table = _coverage_stats_table(sub, thresholds)

            tabs.append(
                pn.Column(
                    pn.pane.Vega(
                        chart, sizing_mode="stretch_width", height=380
                    ),
                    pn.pane.Markdown("**Coverage statistics**"),
                    stats_table,
                    name=label,
                    sizing_mode="stretch_width",
                )
            )

        self.logger.info(
            f"Added {df['chrom'].nunique()} interactive coverage plots from {mosdepth_regions}"
        )
        return pn.Column(header, tabs)
