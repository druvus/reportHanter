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
from ..processors.genomad_processor import GenomadProcessor
from ..processors.kaiju_processor import KaijuPlotGenerator, KaijuProcessor
from ..processors.kraken_processor import KrakenPlotGenerator, KrakenProcessor
from ..processors.quast_processor import QuastProcessor


def _host_kpi_strip(
    flagstat_data: pd.DataFrame,
    flagstat_file: str,
    show_backend_tile: bool = True,
) -> pn.Row:
    """Render the host-alignment headline numbers as a row of KPI
    tiles.

    Reads the parsed flagstat (metric/value DataFrame) for the
    four scalars the panel cares about and infers the host-removal
    backend ("bwa" or "hostile") from the flagstat filename.
    Returns a `pn.Row` of small panes so the strip sits as a
    single horizontal band above the matching bar chart. The
    host species is communicated by the section label above the
    strip, so tile labels stay generic (Total reads / Host
    mapped / ...). ``show_backend_tile`` adds the host-removal
    tool tile; suppress it for the secondary strip since the
    backend is reported once at the primary level.
    """
    lookup = dict(
        zip(flagstat_data["metric"], flagstat_data["value"], strict=False)
    )
    total = int(lookup.get("total_reads", 0))
    pct_mapped = float(lookup.get("percent_mapped", 0.0))
    mapped = int(lookup.get("reads_mapped", round(total * pct_mapped / 100)))
    unmapped = int(lookup.get("reads_unmapped", total - mapped))

    backend = (
        "hostile"
        if "hostile" in flagstat_file.lower()
        else "bwa"
    )

    def _tile(label: str, value: str, accent: str = "#102D5F") -> pn.Column:
        return pn.Column(
            pn.pane.Markdown(
                f"<div style='font-size:11px;color:#666;"
                f"text-transform:uppercase;letter-spacing:0.04em'>"
                f"{label}</div>"
                f"<div style='font-size:22px;color:#222;"
                f"font-weight:600;line-height:1.1'>{value}</div>",
                styles={
                    "padding": "10px 14px",
                    "border-left": f"3px solid {accent}",
                    "background": "#fafafa",
                    "margin": "6px 4px",
                },
                sizing_mode="stretch_width",
            ),
        )

    tiles = [
        _tile("Total reads", f"{total:,}"),
        _tile("Host mapped", f"{mapped:,}"),
        _tile("Non-host reads", f"{unmapped:,}"),
        _tile("% removed", f"{pct_mapped:.1f}%"),
    ]
    if show_backend_tile:
        tiles.append(_tile("Host-removal tool", backend, accent="#13B5A6"))
    return pn.Row(*tiles, sizing_mode="stretch_width")


def _coverage_summary_frame(
    df: pd.DataFrame,
    chrom_to_name: dict[str, str],
    chrom_to_sources: dict[str, str],
    chrom_to_aliases: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Build the per-reference summary DataFrame (no widget).

    Separated from the Tabulator builder so the caller can also
    use the resulting chrom order to drive the per-reference tab
    sequence (so both the summary table and the tab strip share
    `pct_ge_10x` descending sort).
    """
    if df.empty or "depth" not in df.columns:
        return pd.DataFrame(columns=["chrom", "species", "aliases", "sources"])

    aliases_map = chrom_to_aliases or {}
    rows: list[dict[str, str | float | int]] = []
    for chrom, sub in df.groupby("chrom", sort=False):
        window_len = (sub["end"] - sub["start"]).astype(int)
        ref_length = int(window_len.sum())
        total_bases = float((sub["depth"] * window_len).sum())
        mean_depth = total_bases / ref_length if ref_length else 0.0
        bp_ge_5 = int(window_len[sub["depth"] >= 5].sum())
        bp_ge_10 = int(window_len[sub["depth"] >= 10].sum())
        pct_ge_5 = (100.0 * bp_ge_5 / ref_length) if ref_length else 0.0
        pct_ge_10 = (100.0 * bp_ge_10 / ref_length) if ref_length else 0.0
        rows.append(
            {
                "chrom": str(chrom),
                "species": chrom_to_name.get(str(chrom), ""),
                "aliases": aliases_map.get(str(chrom), ""),
                "sources": chrom_to_sources.get(str(chrom), ""),
                "length": ref_length,
                "mean_depth": round(mean_depth, 2),
                "pct_ge_5x": round(pct_ge_5, 1),
                "pct_ge_10x": round(pct_ge_10, 1),
            }
        )

    return (
        pd.DataFrame(rows)
        .sort_values("pct_ge_10x", ascending=False, kind="mergesort")
        .reset_index(drop=True)
    )


def _coverage_header_filters(columns: list[str]) -> dict:
    """Tabulator per-column header filters for the Coverage tables.

    Same client-side semantics as ``_blast_header_filters``: numeric
    columns get a ``>=`` filter, text columns get case-insensitive
    substring match (``like``). Skipping columns absent from the
    rendered view keeps older virusHanter2 outputs working.
    """
    spec: dict[str, dict] = {}
    numeric_ge = {
        "length": ">= length (bp)",
        "mean_depth": ">= mean depth",
        "pct_ge_5x": ">= % >= 5x",
        "pct_ge_10x": ">= % >= 10x",
    }
    for col, placeholder in numeric_ge.items():
        if col in columns:
            spec[col] = {
                "type": "number",
                "func": ">=",
                "placeholder": placeholder,
            }
    text_like = {
        "chrom": "filter accession",
        "species": "filter species",
        "aliases": "filter aliases",
        "sources": "filter sources",
    }
    for col, placeholder in text_like.items():
        if col in columns:
            spec[col] = {"type": "input", "func": "like", "placeholder": placeholder}
    return spec


def _blast_header_filters(columns: list[str]) -> dict:
    """Tabulator per-column header filters for the BLAST contig table.

    Tabulator renders the filter widgets inside each column header
    and applies them client-side, so the controls survive
    ``panel.save()`` without needing a live Python kernel. Numeric
    columns use a ``>=`` filter (type the threshold; rows below it
    disappear); text columns use ``like`` for substring match; the
    ``assembler`` column uses a select-list filter when more than
    one assembler is present.

    Only columns that are actually in the rendered view get a
    filter; unknown columns are silently skipped so the helper
    works on legacy BLAST CSVs that lack the modern column set.
    """
    spec: dict[str, dict] = {}
    # >= filters on the numeric columns scientists routinely
    # threshold on.
    numeric_ge = {
        "percent_identity": ">= % identity",
        "read_len": ">= contig length (bp)",
        "sequence_len": ">= subject length",
        "total_genes": ">= total genes",
        "viral_genes": ">= viral genes",
        "host_genes": ">= host genes",
    }
    for col, placeholder in numeric_ge.items():
        if col in columns:
            spec[col] = {
                "type": "number",
                "func": ">=",
                "placeholder": placeholder,
            }
    # Substring match on free-text columns. ``like`` is Tabulator's
    # case-insensitive contains operator.
    text_like = {
        "match_name": "filter species",
        "aliases": "filter aliases",
        "accession": "filter accession",
    }
    for col, placeholder in text_like.items():
        if col in columns:
            spec[col] = {"type": "input", "func": "like", "placeholder": placeholder}
    # Exact-match on the assembler tag (one of MEGAHIT / metaSPAdes /
    # rnaviralSPAdes). Use a plain input so a reviewer can type
    # ``MEGAHIT`` to isolate one assembler.
    if "assembler" in columns:
        spec["assembler"] = {"type": "input", "func": "like", "placeholder": "filter assembler"}
    # Boolean-ish provirus flag from CheckV.
    if "provirus" in columns:
        spec["provirus"] = {"type": "input", "func": "like", "placeholder": "Yes / No"}
    return spec


def _apply_canonical_blast_names(
    frame: pd.DataFrame,
    virus_names: str | Path | None,
    logger: logging.Logger | None = None,
) -> pd.DataFrame:
    """Swap the legacy BLAST match_name for the ICTV-canonical
    species name carried by the virus_names sidecar.

    BLAST CSVs produced before the upstream canonicalisation rule
    (or for samples where the canonicaliser had nothing to add)
    carry the legacy NCBI scientific name in ``match_name`` and
    no ``aliases`` column. When the ``virus_names`` TSV is
    supplied, look up each row's ``accession`` against the
    sidecar's ``chrom`` column (stripped of any version suffix);
    on a hit, swap in the canonical ``name`` as the new
    ``match_name`` and prepend the original legacy name to the
    row's aliases. Rows without a hit are left untouched.

    Shared by the Dashboard top-5 BLAST card and the Assembly
    classification contig table so both surface the same canonical
    species names.
    """
    if (
        not virus_names
        or frame.empty
        or "accession" not in frame.columns
        or "match_name" not in frame.columns
    ):
        return frame
    try:
        sidecar = pd.read_csv(virus_names, sep="\t")
    except Exception as exc:  # noqa: BLE001
        if logger is not None:
            logger.warning(f"Could not read virus-names sidecar {virus_names}: {exc}")
        return frame
    if not {"chrom", "name"}.issubset(sidecar.columns):
        return frame
    base_chrom = sidecar["chrom"].astype(str).str.split(".").str[0]
    name_map = dict(zip(base_chrom, sidecar["name"].astype(str), strict=False))
    alias_map: dict[str, str] = {}
    if "aliases" in sidecar.columns:
        alias_map = dict(
            zip(base_chrom, sidecar["aliases"].fillna("").astype(str), strict=False)
        )
    out = frame.copy()
    out_accession = out["accession"].astype(str).str.split(".").str[0]
    canonical = out_accession.map(name_map)
    hit = canonical.notna() & canonical.ne("")
    if not hit.any():
        return frame
    legacy_match = out["match_name"].astype(str)
    existing_aliases = (
        out["aliases"].fillna("").astype(str)
        if "aliases" in out.columns
        else pd.Series([""] * len(out), index=out.index)
    )
    sidecar_aliases = out_accession.map(alias_map).fillna("")

    def _compose(legacy: str, sidecar_a: str, existing: str) -> str:
        parts: list[str] = []
        for chunk in (legacy, sidecar_a, existing):
            for token in chunk.split(";"):
                token = token.strip()
                if token and token not in parts:
                    parts.append(token)
        return "; ".join(parts)

    out.loc[hit, "match_name"] = canonical[hit]
    new_aliases = [
        _compose(legacy, sidecar_a, existing) if h else existing
        for legacy, sidecar_a, existing, h in zip(
            legacy_match, sidecar_aliases, existing_aliases, hit, strict=False
        )
    ]
    out["aliases"] = new_aliases
    return out


def _ncbi_nuccore_link_formatter() -> dict:
    """Tabulator link-formatter spec that turns a cell's value
    into ``https://www.ncbi.nlm.nih.gov/nuccore/<value>`` and
    opens the link in a new browser tab.

    Tabulator's ``link`` formatter combines the cell's value with
    a ``urlPrefix`` to build the href, leaving the cell text as
    the value itself. The link survives the static HTML save
    because it is rendered client-side by Tabulator.js.
    """
    return {
        "type": "link",
        "urlPrefix": "https://www.ncbi.nlm.nih.gov/nuccore/",
        "target": "_blank",
    }


def _coverage_summary_table(
    summary_df: pd.DataFrame,
) -> pn.widgets.Tabulator:
    """Render the per-reference summary as a paginated Tabulator.

    Sortable by the reviewer (Tabulator's client-side sort
    survives the static HTML save), clipboard-copy enabled. The
    row order at render time defines the tab order below; the
    reviewer can re-sort by any column and still find the
    corresponding tab by row position in the *default* sort
    because the tabs are pinned to that order at build time.

    The ``chrom`` cell renders as a link to the NCBI Nucleotide
    record so a reviewer can pop a reference's GenBank entry
    open without leaving the report.
    """
    formatters: dict = {}
    if "chrom" in summary_df.columns:
        formatters["chrom"] = _ncbi_nuccore_link_formatter()
    return pn.widgets.Tabulator(
        summary_df,
        disabled=True,
        show_index=False,
        layout="fit_columns",
        pagination="local",
        page_size=15,
        formatters=formatters,
        header_filters=_coverage_header_filters(list(summary_df.columns)),
        configuration={
            "clipboard": True,
            "clipboardCopyRowRange": "active",
        },
    )


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
        """Render a section banner in the brand palette.

        White card with navy text and a teal left rule, replacing
        the earlier dark-green band so the report reads as a clean
        light-themed dashboard consistent with the new wordmark.
        """
        primary = self.config.get("report.primary_color", "#102D5F")
        accent = self.config.get("report.accent_color", "#13B5A6")
        return pn.pane.Markdown(
            text,
            styles={
                "color": primary,
                "padding": "10px 15px 10px 18px",
                "text-align": "left",
                "font-size": "16px",
                "background": "#ffffff",
                "border-left": f"4px solid {accent}",
                "margin": "10px",
                "border-radius": "4px",
                "box-shadow": "0 1px 2px rgba(0,0,0,0.04)",
            },
        )

    def _filters_block(self, lines: list[str]) -> pn.pane.Markdown:
        """Small read-only block listing the active filter thresholds.

        Rendered below the section header so the reader knows which
        cutoffs produced the plots without having to rerun the pipeline.
        """
        accent = self.config.get("report.accent_color", "#13B5A6")
        body = "\n".join(f"- {line}" for line in lines)
        return pn.pane.Markdown(
            f"**Filters applied**\n\n{body}",
            styles={
                "font-size": "12px",
                "padding": "4px 12px",
                "margin": "0 10px 10px 10px",
                "color": "#333",
                "background": "#f3f3f3",
                "border-left": f"3px solid {accent}",
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
        primary_host = kwargs.get("primary_host") or "Human"
        secondary_host = kwargs.get("secondary_host") or "Secondary"
        if not flagstat_file:
            raise ValueError("flagstat_file is required")

        flagstat_processor = FlagstatProcessor(self.config.get_config("flagstat"))
        flagstat_data = flagstat_processor.process(flagstat_file)
        primary_pane = flagstat_processor.create_alignment_chart(
            flagstat_data, primary_host
        )

        # KPI tile strip with the headline numbers (total reads,
        # host mapped, non-host, % removed) plus the backend label
        # inferred from the flagstat filename (hostile writes
        # ``hostile_contamination_flagstat.txt``; bwa writes
        # ``human_contamination_flagstat.txt``). The host species
        # name is carried in the section label above so the
        # reviewer can see which reference the numbers describe.
        primary_kpis = _host_kpi_strip(flagstat_data, str(flagstat_file))

        components: list = [
            pn.pane.Markdown(
                f"**Primary host alignment - {primary_host}**",
                styles={"margin": "0 10px 4px 10px"},
            ),
            primary_kpis,
            primary_pane,
        ]
        if secondary_flagstat_file:
            secondary_data = flagstat_processor.process(secondary_flagstat_file)
            secondary_pane = flagstat_processor.create_alignment_chart(
                secondary_data, secondary_host
            )
            secondary_kpis = _host_kpi_strip(
                secondary_data,
                str(secondary_flagstat_file),
                show_backend_tile=False,
            )
            components.extend(
                [
                    pn.layout.Divider(),
                    pn.pane.Markdown(
                        f"**Secondary host alignment - {secondary_host}**",
                        styles={"margin": "0 10px 4px 10px"},
                    ),
                    secondary_kpis,
                    secondary_pane,
                ]
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
            ## Assembly statistics
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
        # Per-assembler labels + frames collected as we iterate so
        # the optional Comparison tab can stitch them together
        # without re-parsing the QUAST files.
        per_assembler: list[tuple[str, pd.DataFrame]] = []
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
                per_assembler.append((label, quast_data))
                tab_panes.append(
                    quast_processor.create_summary_table(
                        quast_data, name=label
                    )
                )
            except Exception as e:  # noqa: BLE001
                self.logger.warning(
                    f"Could not render QUAST report {qpath}: {e}"
                )

        # Comparison sub-tab pinned at the front when more than one
        # assembler contributed a report. Rows are the QUAST
        # highlight metrics (driven by ``QuastProcessor.highlighted``
        # so the metric set always matches the per-assembler tabs)
        # and columns are one per assembler — lets the reviewer
        # contrast N50, # contigs, GC%, etc. across assemblers in a
        # single view.
        if len(per_assembler) >= 2:
            quast_processor = QuastProcessor(self.config.get_config("quast"))
            merged: pd.DataFrame | None = None
            for label, frame in per_assembler:
                highlight = quast_processor.highlighted(frame).copy()
                value_col = (
                    highlight.columns[1]
                    if len(highlight.columns) >= 2
                    else None
                )
                if value_col is None:
                    continue
                highlight = highlight[
                    [quast_processor.METRIC_COLUMN, value_col]
                ].rename(columns={value_col: label})
                merged = (
                    highlight
                    if merged is None
                    else merged.merge(
                        highlight,
                        on=quast_processor.METRIC_COLUMN,
                        how="outer",
                    )
                )
            if merged is not None and not merged.empty:
                comparison = pn.widgets.Tabulator(
                    merged,
                    layout="fit_columns",
                    pagination=None,
                    show_index=False,
                    disabled=True,
                    name="Comparison",
                )
                tab_panes.insert(0, comparison)

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
        virus_names = kwargs.get("virus_names")

        if not blastn_files:
            raise ValueError("blastn_files is required")

        # Process BLAST data — concatenate one frame per assembler so
        # the contig table and the headline bar chart carry the union
        # of contigs with their assembler tag.
        blast_processor = BlastProcessor(self.config.get_config("blast"))
        blast_plot_generator = BlastPlotGenerator(self.config.get_config("plotting"))

        # Per-assembler BLAST CSVs from virusHanter2's multi-assembler
        # mode carry an explicit ``assembler`` column. Older / single-
        # assembler runs do not; try to infer the assembler from the
        # CSV's path (any segment matching a known assembler name).
        # When inference fails we leave the column unset rather than
        # writing "unknown" — ``_table_view`` then suppresses the
        # column so the contig table is not cluttered with a useless
        # "unknown" repeated on every row.
        known_assemblers = {"MEGAHIT", "metaSPAdes", "rnaviralSPAdes", "SPAdes"}
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
                inferred = next(
                    (seg for seg in Path(str(path)).parts if seg in known_assemblers),
                    None,
                )
                if inferred:
                    frame = frame.assign(assembler=inferred)
            per_assembler_frames.append(frame)
        blast_data = (
            pd.concat(per_assembler_frames, ignore_index=True)
            if per_assembler_frames
            else pd.DataFrame()
        )
        # Swap any legacy NCBI match_name for the ICTV-canonical name
        # carried by the virus_names sidecar, pushing the legacy name
        # into the aliases column. Same rule the Dashboard top-5 BLAST
        # card applies, so both views surface the same species labels.
        blast_data = _apply_canonical_blast_names(
            blast_data, virus_names, self.logger
        )

        def _table_view(frame: pd.DataFrame) -> pd.DataFrame:
            """Drop bookkeeping columns and pin the identifier columns.

            The BLAST CSV's ``name`` column carries the contig
            identifier (e.g. ``k57_148_pilon``). Rename to
            ``seq_name`` so the contig table matches the geNomad
            sub-tab, which already uses that column name. The
            ``assembler`` column is dropped when no row carries a
            value (single-assembler run with no path-derived label),
            since a column of empty cells adds no information.

            Kept as a closure so the assembler-filter callback can
            project the filtered BLAST frame through exactly the same
            column shape as the initial render.
            """
            if frame.empty:
                return pd.DataFrame({"sequence": ["NO SEQUENCES GENERATED"]})
            # Drop bookkeeping columns and the audit-only "_raw"
            # columns the upstream canonicaliser keeps alongside the
            # ICTV-canonical match_name. The raw stitle in `matches`
            # and the un-canonicalised name in `match_name_raw` are
            # still present in the on-disk CSV for audit; only the
            # rendered Tabulator (and therefore the HTML) hides them
            # so the viewer does not see two different names for the
            # same species.
            columns_to_drop = [
                "matches",
                "sample_id",
                "match_name_raw",
            ]
            view = frame.drop(
                columns=[col for col in columns_to_drop if col in frame.columns]
            )
            if "name" in view.columns:
                view = view.rename(columns={"name": "seq_name"})
            if "assembler" in view.columns and view["assembler"].isna().all():
                view = view.drop(columns=["assembler"])
            front = [c for c in ("assembler", "seq_name") if c in view.columns]
            others = [c for c in view.columns if c not in front]
            view = view[front + others]
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
        # `accession` carries NCBI nucleotide accessions (e.g.
        # NC_009334). Linkify so a reviewer can click straight
        # through to the NCBI Nucleotide record. Opens in a new
        # tab so the report's own tab stays put.
        if "accession" in table_data.columns:
            formatters["accession"] = _ncbi_nuccore_link_formatter()

        blast_table = pn.widgets.Tabulator(
            table_data,
            formatters=formatters,
            header_filters=_blast_header_filters(list(table_data.columns)),
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
            ## Assembly classification
            Contigs from de novo assembly are classified with
            BLASTN. {counts_line} When geNomad is enabled in the
            pipeline, a per-assembler geNomad section is appended
            beneath the BLAST charts and table. Each column header
            on the contig table carries a filter widget: type a
            number into ``percent_identity`` or ``read_len`` to
            keep only rows above that threshold, or a substring
            into ``match_name`` / ``aliases`` to narrow to a
            species. Filters compose; clear a box to drop the
            constraint. Select rows and press Ctrl/Cmd-C to copy
            the visible (filtered) rows to the clipboard.
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
        # Map geNomad summary paths to the assembler that produced
        # them so each per-assembler tab can carry its own nested
        # geNomad sub-tab. virusHanter2 emits genomad under
        # ``<sample>/<assembler>/GENOMAD/...``; the assembler name is
        # the path segment immediately preceding ``GENOMAD``.
        genomad_by_assembler: dict[str, str | Path] = {}
        for gpath in genomad_summaries or []:
            parts = Path(str(gpath)).parts
            try:
                idx = next(i for i, seg in enumerate(parts) if seg.upper() == "GENOMAD")
            except StopIteration:
                continue
            if idx >= 1:
                genomad_by_assembler[parts[idx - 1]] = gpath

        def _genomad_pane(asm_name: str) -> pn.viewable.Viewable | None:
            gpath = genomad_by_assembler.get(asm_name)
            if not gpath:
                return None
            try:
                gp = GenomadProcessor(self.config.get_config("genomad"))
                gdf = gp.process(gpath)
                return gp.create_summary_table(gdf)
            except Exception as e:  # noqa: BLE001
                self.logger.warning(f"Could not render geNomad summary {gpath}: {e}")
                return None

        def _build_assembler_tab(name: str, frame: pd.DataFrame) -> pn.Column:
            # Two separate bar charts so each metric carries its own
            # title and axis. The earlier consolidation overlaid
            # count as a text label on the bp chart, which read as
            # ambiguous ("the chart title says bp but the labels
            # look like the metric"). Splitting them is clearer:
            # one chart per question.
            count_plot = blast_plot_generator.generate_plot(frame)
            bp_plot = blast_plot_generator.create_bp_chart(frame)
            sub_table_view = _table_view(frame)
            sub_table = pn.widgets.Tabulator(
                sub_table_view,
                formatters=formatters,
                header_filters=_blast_header_filters(list(sub_table_view.columns)),
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
            parts: list = [
                pn.pane.Markdown(
                    "**Number of contigs per BLAST match**",
                    styles={"margin": "8px 10px 0 10px"},
                ),
                pn.pane.Vega(
                    count_plot,
                    sizing_mode="stretch_width",
                ),
                pn.pane.Markdown(
                    "**Cumulative contig length per BLAST match (bp)**",
                    styles={"margin": "14px 10px 0 10px"},
                ),
                pn.pane.Vega(
                    bp_plot,
                    sizing_mode="stretch_width",
                ),
                pn.pane.Markdown(
                    "**BLAST contig annotation table** - one row per "
                    "contig with its BLAST match, percent identity, "
                    "contig length and accession. Column headers carry "
                    "filter widgets; select rows and press Ctrl/Cmd-C "
                    "to copy the visible rows to the clipboard.",
                    styles={"margin": "14px 10px 0 10px"},
                ),
                sub_table,
            ]
            genomad_pane = _genomad_pane(name)
            if genomad_pane is not None:
                # Flatten geNomad into the same column under its own
                # header rather than as a nested sub-tab, so the
                # reviewer can scan BLAST then geNomad without
                # switching tabs inside an assembler tab.
                parts.extend(
                    [
                        pn.layout.Divider(),
                        pn.pane.Markdown(
                            "### geNomad viral-contig calls",
                            styles={"margin": "12px 10px 0 10px"},
                        ),
                        pn.pane.Markdown(
                            "*One row per contig geNomad called viral, "
                            "sorted by ``virus_score`` descending. "
                            "Complements BLAST: a contig can be called "
                            "viral by geNomad without a BLAST match if "
                            "no close reference is in the BLAST DB.*",
                            styles={"margin": "0 10px 4px 10px", "font-size": "12px"},
                        ),
                        genomad_pane,
                    ]
                )
            return pn.Column(*parts, name=name, sizing_mode="stretch_width")

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

        # geNomad summaries are nested inside each per-assembler tab
        # by ``_build_assembler_tab`` above, so the top-level tab strip
        # stays linear regardless of how many assemblers were run.
        # In the single-assembler fallback path (BLASTN + table only)
        # geNomad is appended as a top-level sibling.
        if not (len(present_assemblers) > 1) and genomad_summaries:
            for asm in genomad_by_assembler:
                pane = _genomad_pane(asm)
                if pane is not None:
                    tab_panes.append(pane)

        tabs = pn.Tabs(*tab_panes)
        return pn.Column(header, tabs)


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

        header = self._create_header(
            """
            ## Alignment coverage
            Per-reference coverage from mosdepth, one sub-tab per
            reference, ordered by breadth at >= 10x desc. The
            companion summary table lists the same references in the
            same order so row N matches tab N.
            """
        )
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
        chrom_to_aliases: dict[str, str] = {}
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
                # Optional `aliases` column added when the upstream
                # canonicaliser collected the legacy NCBI scientific
                # name plus acronyms / common names from names.dmp
                # alongside the ICTV-binomial. Carried into the
                # Coverage summary tables and the Dashboard so
                # scientists can still recognise renamed species.
                if "aliases" in names_df.columns:
                    chrom_to_aliases = dict(
                        zip(
                            names_df["chrom"].astype(str),
                            names_df["aliases"].fillna("").astype(str),
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
        filters = self._filters_block(
            [
                "Depth thresholds: "
                + ", ".join(f"{t}x" for t in thresholds),
                "Reference window size set by virusHanter2 COVERAGE_WINDOW "
                "(default 100 windows per reference).",
                "References ordered by % bp >= 10x (descending).",
            ]
        )

        # Build the summary frame first; its row order (sorted by
        # ``% >= 10x`` descending) drives both the summary
        # Tabulator at the top AND the per-reference tab order
        # below so the two views always line up.
        summary_df = _coverage_summary_frame(
            df, chrom_to_name, chrom_to_sources, chrom_to_aliases
        )
        chrom_order: list[str] = summary_df["chrom"].astype(str).tolist()
        df = df.copy()
        df["chrom"] = df["chrom"].astype(str)
        by_chrom = {c: g for c, g in df.groupby("chrom", sort=False)}

        for chrom in chrom_order:
            sub = by_chrom.get(chrom)
            if sub is None or sub.empty:
                continue
            chart = plot_generator.generate_plot(sub, chrom=str(chrom)).interactive()
            species = chrom_to_name.get(str(chrom), "")
            sources = chrom_to_sources.get(str(chrom), "")
            base = f"{chrom} — {species}" if species else str(chrom)
            full_label = f"{base} [{sources}]" if sources else base
            # Keep the left-rail tab strip readable: species names
            # plus an optional source tag can run to 60+ characters
            # and wrap onto multiple lines. Cap the on-tab label at
            # 38 chars; the per-reference statistics table directly
            # below carries the full label without truncation.
            label = full_label if len(full_label) <= 38 else full_label[:35] + "..."

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

        # Per-reference summary table, sorted by % >= 10x
        # descending. Both the summary row order and the per-tab
        # order below derive from ``chrom_order`` so the two
        # views always agree: row N in the table corresponds to
        # tab N in the strip below.
        #
        # Note on click-to-drill: Panel's Tabulator ``selection``
        # parameter cannot be js-linked to a ``Tabs.active`` index
        # in static HTML (it needs a live Python kernel). The
        # matched ordering is the workable substitute — the
        # reviewer reads the table, notes the row index, and
        # clicks the matching tab below at the same position.
        summary_table = _coverage_summary_table(summary_df)
        summary_block = pn.Column(
            pn.pane.Markdown(
                "**Coverage summary** — one row per reference, "
                "sorted by `% >= 10x` descending. The tabs below "
                "follow the same order: row 1 here is the first "
                "tab below, row 2 the second, and so on.",
                styles={"margin": "0 10px 4px 10px"},
            ),
            summary_table,
            sizing_mode="stretch_width",
        )

        return pn.Column(header, filters, summary_block, pn.layout.Divider(), tabs)
