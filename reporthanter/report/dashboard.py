"""Dashboard landing section.

Renders a compact, single-viewport summary of the per-sample run
intended as the first tab in the report. Pulls headline numbers
from the same processors that drive the six detail tabs so the
values shown here cannot drift from the detail views.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd
import panel as pn

from ..core.config import DefaultConfig
from ..core.exceptions import DataProcessingError, FileValidationError
from ..core.interfaces import ReportSection
from ..processors.blast_processor import BlastProcessor
from ..processors.coverage_processor import CoverageProcessor
from ..processors.flagstat_processor import FlagstatProcessor
from ..processors.kaiju_processor import KaijuProcessor
from ..processors.kraken_processor import KrakenProcessor
from ..processors.quast_processor import QuastProcessor
from .sections import (
    _apply_canonical_blast_names,
    _coverage_summary_frame,
    _ncbi_nuccore_link_formatter,
)


def _tile(label: str, value: str, accent: str = "#102D5F") -> pn.pane.Markdown:
    """One KPI tile, matching the style of ``_host_kpi_strip``."""
    return pn.pane.Markdown(
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
    )


def _compact_table(
    frame: pd.DataFrame,
    *,
    name: str,
    formatters: dict | None = None,
) -> pn.widgets.Tabulator:
    """Small, non-paginated Tabulator used for the Dashboard tiles."""
    return pn.widgets.Tabulator(
        frame,
        disabled=True,
        show_index=False,
        layout="fit_columns",
        pagination=None,
        formatters=formatters or {},
        name=name,
        configuration={"clipboard": True},
    )


class DashboardSection(ReportSection):
    """First-tab landing summary."""

    def __init__(self, config: DefaultConfig | None = None):
        self.config = config or DefaultConfig()
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    def section_name(self) -> str:
        return "Dashboard"

    def generate_section(self, **kwargs: Any) -> pn.Column:
        sample_name = kwargs.get("sample_name") or "Sample"
        fastp_json = kwargs.get("fastp_json")
        flagstat_file = kwargs.get("flagstat_file")
        kraken_file = kwargs.get("kraken_file")
        kaiju_table = kwargs.get("kaiju_table")
        blastn_files = kwargs.get("blastn_files") or []
        quast_reports = kwargs.get("quast_reports") or []
        mosdepth_regions = kwargs.get("mosdepth_regions")
        virus_names = kwargs.get("virus_names")

        primary = self.config.get("report.primary_color", "#102D5F")
        accent = self.config.get("report.accent_color", "#13B5A6")
        header = pn.pane.Markdown(
            "## Dashboard",
            styles={
                "color": primary,
                "padding": "10px 15px 10px 18px",
                "font-size": "16px",
                "background": "#ffffff",
                "border-left": f"4px solid {accent}",
                "margin": "10px",
                "border-radius": "4px",
                "box-shadow": "0 1px 2px rgba(0,0,0,0.04)",
            },
        )

        sample_band = self._sample_band(
            sample_name=sample_name,
            flagstat_file=flagstat_file,
            quast_reports=quast_reports,
        )

        kpi_row = self._kpi_strip(
            fastp_json=fastp_json,
            flagstat_file=flagstat_file,
            kraken_file=kraken_file,
            blastn_files=blastn_files,
        )

        top_hits = self._top_hits_row(
            kraken_file=kraken_file,
            kaiju_table=kaiju_table,
            blastn_files=blastn_files,
            virus_names=virus_names,
        )

        assembly_summary = self._assembly_summary(quast_reports)

        coverage_top = self._coverage_top(mosdepth_regions, virus_names)

        return pn.Column(
            header,
            sample_band,
            kpi_row,
            pn.layout.Divider(),
            pn.pane.Markdown("### Top viral hits", styles={"margin": "0 10px"}),
            top_hits,
            pn.layout.Divider(),
            pn.pane.Markdown("### Assembly summary", styles={"margin": "0 10px"}),
            assembly_summary,
            pn.layout.Divider(),
            pn.pane.Markdown("### Best-covered references", styles={"margin": "0 10px"}),
            coverage_top,
        )

    # -- band + tiles ----------------------------------------------------

    def _sample_band(
        self,
        *,
        sample_name: str,
        flagstat_file: str | Path | None,
        quast_reports: list[str | Path],
    ) -> pn.pane.Markdown:
        backend = "hostile" if flagstat_file and "hostile" in str(flagstat_file).lower() else "bwa"
        assemblers: list[str] = []
        for path in quast_reports:
            parts = Path(str(path)).parts
            if len(parts) >= 3:
                assemblers.append(parts[-3])
        asm_str = ", ".join(assemblers) if assemblers else "none"
        return pn.pane.Markdown(
            f"Host removal: `{backend}` - assemblers: `{asm_str}`",
            styles={"margin": "0 10px 6px 10px", "font-size": "13px"},
        )

    def _kpi_strip(
        self,
        *,
        fastp_json: str | Path | None,
        flagstat_file: str | Path | None,
        kraken_file: str | Path | None,
        blastn_files: list[str | Path],
    ) -> pn.Row:
        total_raw = "n/a"
        q30 = "n/a"
        if fastp_json:
            try:
                with open(fastp_json) as handle:
                    fastp = json.load(handle)
                after = fastp.get("summary", {}).get("after_filtering", {})
                total_raw_n = int(after.get("total_reads", 0))
                total_raw = f"{total_raw_n / 1000:.1f} K" if total_raw_n else "0"
                q30 = f"{after.get('q30_rate', 0) * 100:.1f}%"
            except (
                OSError,
                json.JSONDecodeError,
                ValueError,
                KeyError,
                DataProcessingError,
                FileValidationError,
            ) as exc:
                self.logger.warning(f"Could not read fastp JSON {fastp_json}: {exc}")

        pct_host = "n/a"
        non_host = "n/a"
        if flagstat_file:
            try:
                processor = FlagstatProcessor(self.config.get_config("flagstat"))
                frame = processor.process(flagstat_file)
                lookup = dict(zip(frame["metric"], frame["value"], strict=False))
                pct = float(lookup.get("percent_mapped", 0.0))
                total = int(lookup.get("total_reads", 0))
                mapped = int(lookup.get("reads_mapped", round(total * pct / 100)))
                pct_host = f"{pct:.1f}%"
                non_host = f"{(total - mapped):,}"
            except (
                OSError,
                json.JSONDecodeError,
                ValueError,
                KeyError,
                DataProcessingError,
                FileValidationError,
            ) as exc:
                self.logger.warning(f"Could not read flagstat {flagstat_file}: {exc}")

        kraken_pct = "n/a"
        if kraken_file:
            try:
                kp = KrakenProcessor(self.config.get_config("kraken"))
                kdata = kp.process(kraken_file)
                # virus_only is structural for this card and overrides
                # whatever the user config sets.
                kraken_cfg = {**self.config.get_config("filtering.kraken"), "virus_only": True}
                _filt, unclassified = kp.filter_data(kdata, **kraken_cfg)
                kraken_pct = f"{(1.0 - float(unclassified)) * 100:.1f}%"
            except (
                OSError,
                json.JSONDecodeError,
                ValueError,
                KeyError,
                DataProcessingError,
                FileValidationError,
            ) as exc:
                self.logger.warning(f"Could not summarise Kraken {kraken_file}: {exc}")

        contig_total = 0
        if blastn_files:
            bp = BlastProcessor(self.config.get_config("blast"))
            for path in blastn_files:
                try:
                    frame = bp.process(path)
                    contig_total += int(len(frame))
                except (
                    OSError,
                    json.JSONDecodeError,
                    ValueError,
                    KeyError,
                    DataProcessingError,
                    FileValidationError,
                ) as exc:
                    self.logger.warning(f"Could not read BLAST CSV {path}: {exc}")

        return pn.Row(
            _tile("Total reads", total_raw),
            _tile("Q30 rate", q30),
            _tile("% host removed", pct_host),
            _tile("Non-host reads", non_host),
            _tile("Reads classified (Kraken viral)", kraken_pct, accent="#13B5A6"),
            _tile("Classified contigs", f"{contig_total:,}", accent="#13B5A6"),
            sizing_mode="stretch_width",
        )

    # -- top hits --------------------------------------------------------

    def _top_hits_row(
        self,
        *,
        kraken_file: str | Path | None,
        kaiju_table: str | Path | None,
        blastn_files: list[str | Path],
        virus_names: str | Path | None = None,
    ) -> pn.Row:
        # Cards may render either a populated table or a single
        # "no data" line; the height difference would otherwise leave
        # a ragged row baseline. Pin each card to the same minimum
        # height so the row stays aligned.
        kraken_card = self._kraken_card(kraken_file)
        kaiju_card = self._kaiju_card(kaiju_table)
        blast_card = self._blast_card(blastn_files, virus_names=virus_names)
        for card in (kraken_card, kaiju_card, blast_card):
            card.min_height = 220
        return pn.Row(kraken_card, kaiju_card, blast_card, sizing_mode="stretch_width")

    def _kraken_card(self, kraken_file: str | Path | None) -> pn.Column:
        caption = pn.pane.Markdown(
            "**Top 5 Kraken species (virus-only)** - see *Classification of "
            "reads* for the full chart.",
            styles={"margin": "0 6px 4px 6px", "font-size": "12px"},
        )
        if not kraken_file:
            return pn.Column(caption, pn.pane.Markdown("*No Kraken data.*"))
        try:
            kp = KrakenProcessor(self.config.get_config("kraken"))
            kdata = kp.process(kraken_file)
            config = dict(self.config.get_config("filtering.kraken"))
            config["max_entries"] = 5
            config["virus_only"] = True
            filt, _ = kp.filter_data(kdata, **config)
            cols = ["name", "percent", "count_clades"]
            if "aliases" in filt.columns:
                cols.append("aliases")
            view = filt[cols].assign(percent=lambda d: (d["percent"] * 100).round(2))
            # Drop sub-1% rows: noise hits clutter the landing card.
            min_pct = self.config.get("filtering.dashboard_min_pct", 1.0)
            view = view.loc[view["percent"] >= min_pct]
            if view.empty:
                return pn.Column(
                    caption,
                    pn.pane.Markdown("*No Kraken species at >= 1% of reads.*"),
                )
            return pn.Column(
                caption,
                _compact_table(view, name="Top Kraken species"),
                sizing_mode="stretch_width",
            )
        except (
            OSError,
            json.JSONDecodeError,
            ValueError,
            KeyError,
            DataProcessingError,
            FileValidationError,
        ) as exc:
            self.logger.warning(f"Kraken summary failed: {exc}")
            return pn.Column(caption, pn.pane.Markdown("*Kraken summary unavailable.*"))

    def _kaiju_card(self, kaiju_table: str | Path | None) -> pn.Column:
        caption = pn.pane.Markdown(
            "**Top 5 Kaiju taxa** - see *Classification of reads* for the full chart.",
            styles={"margin": "0 6px 4px 6px", "font-size": "12px"},
        )
        if not kaiju_table:
            return pn.Column(caption, pn.pane.Markdown("*No Kaiju data.*"))
        try:
            kp = KaijuProcessor(self.config.get_config("kaiju"))
            kdata = kp.process(kaiju_table)
            config = dict(self.config.get_config("filtering.kaiju"))
            config["max_entries"] = 5
            filt, _ = kp.filter_data(kdata, **config)
            cols = ["taxon_name", "percent", "reads"]
            if "aliases" in filt.columns:
                cols.append("aliases")
            view = filt[cols].assign(percent=lambda d: (d["percent"] * 100).round(2))
            # Drop sub-1% rows: noise hits clutter the landing card.
            min_pct = self.config.get("filtering.dashboard_min_pct", 1.0)
            view = view.loc[view["percent"] >= min_pct]
            if view.empty:
                return pn.Column(
                    caption,
                    pn.pane.Markdown("*No Kaiju taxa at >= 1% of reads.*"),
                )
            return pn.Column(
                caption,
                _compact_table(view, name="Top Kaiju taxa"),
                sizing_mode="stretch_width",
            )
        except (
            OSError,
            json.JSONDecodeError,
            ValueError,
            KeyError,
            DataProcessingError,
            FileValidationError,
        ) as exc:
            self.logger.warning(f"Kaiju summary failed: {exc}")
            return pn.Column(caption, pn.pane.Markdown("*Kaiju summary unavailable.*"))

    def _blast_card(
        self,
        blastn_files: list[str | Path],
        *,
        virus_names: str | Path | None = None,
    ) -> pn.Column:
        caption = pn.pane.Markdown(
            "**Top 5 BLAST matches by cumulative bp** - see *Assembly "
            "classification* for the contig-level table.",
            styles={"margin": "0 6px 4px 6px", "font-size": "12px"},
        )
        if not blastn_files:
            return pn.Column(caption, pn.pane.Markdown("*No BLAST data.*"))
        bp = BlastProcessor(self.config.get_config("blast"))
        frames: list[pd.DataFrame] = []
        for path in blastn_files:
            try:
                frames.append(bp.process(path))
            except (
                OSError,
                json.JSONDecodeError,
                ValueError,
                KeyError,
                DataProcessingError,
                FileValidationError,
            ) as exc:
                self.logger.warning(f"BLAST card: could not read {path}: {exc}")
        if not frames:
            return pn.Column(caption, pn.pane.Markdown("*BLAST summary unavailable.*"))
        merged = pd.concat(frames, ignore_index=True)
        merged = _apply_canonical_blast_names(merged, virus_names, self.logger)
        top = bp.top_matches_by_bp(merged, n=5)
        if top.empty:
            return pn.Column(caption, pn.pane.Markdown("*No classified contigs.*"))
        return pn.Column(
            caption,
            _compact_table(top, name="Top BLAST matches"),
            sizing_mode="stretch_width",
        )

    # -- assembly --------------------------------------------------------

    def _assembly_summary(self, quast_reports: list[str | Path]) -> pn.viewable.Viewable:
        if not quast_reports:
            return pn.pane.Markdown(
                "*No QUAST reports - assembly disabled in the run.*",
                styles={"margin": "0 10px"},
            )
        qp = QuastProcessor(self.config.get_config("quast"))
        keep = ("# contigs", "Largest contig", "Total length", "N50")
        rows: list[dict[str, object]] = []
        for path in quast_reports:
            try:
                frame = qp.process(path)
                highlight = qp.highlighted(frame)
                lookup = dict(
                    zip(highlight[qp.METRIC_COLUMN], highlight[qp.VALUE_COLUMN], strict=False)
                )
                parts = Path(str(path)).parts
                label = parts[-3] if len(parts) >= 3 else Path(path).stem
                row: dict[str, object] = {"Assembler": label}
                for metric in keep:
                    row[metric] = lookup.get(metric, "")
                rows.append(row)
            except (
                OSError,
                json.JSONDecodeError,
                ValueError,
                KeyError,
                DataProcessingError,
                FileValidationError,
            ) as exc:
                self.logger.warning(f"Assembly summary: could not parse {path}: {exc}")
        if not rows:
            return pn.pane.Markdown("*QUAST reports could not be parsed.*")
        view = pd.DataFrame(rows, columns=["Assembler", *keep])
        return _compact_table(view, name="Assembly summary")

    # -- coverage --------------------------------------------------------

    def _coverage_top(
        self,
        mosdepth_regions: str | Path | None,
        virus_names: str | Path | None,
    ) -> pn.viewable.Viewable:
        if not mosdepth_regions:
            return pn.pane.Markdown("*No coverage data.*", styles={"margin": "0 10px"})
        try:
            processor = CoverageProcessor(self.config.get_config("coverage"))
            df = processor.process(mosdepth_regions)
        except (
            OSError,
            json.JSONDecodeError,
            ValueError,
            KeyError,
            DataProcessingError,
            FileValidationError,
        ) as exc:
            self.logger.warning(f"Coverage summary failed: {exc}")
            return pn.pane.Markdown("*Coverage summary unavailable.*")
        if df.empty:
            return pn.pane.Markdown("*No references aligned.*", styles={"margin": "0 10px"})
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
                if "sources" in names_df.columns:
                    chrom_to_sources = dict(
                        zip(
                            names_df["chrom"].astype(str),
                            names_df["sources"].fillna("").astype(str),
                            strict=False,
                        )
                    )
                if "aliases" in names_df.columns:
                    chrom_to_aliases = dict(
                        zip(
                            names_df["chrom"].astype(str),
                            names_df["aliases"].fillna("").astype(str),
                            strict=False,
                        )
                    )
            except (
                OSError,
                json.JSONDecodeError,
                ValueError,
                KeyError,
                DataProcessingError,
                FileValidationError,
            ) as exc:
                self.logger.warning(f"Could not read virus-names sidecar {virus_names}: {exc}")
        summary = _coverage_summary_frame(df, chrom_to_name, chrom_to_sources, chrom_to_aliases)
        if summary.empty:
            return pn.pane.Markdown("*No references aligned.*")
        # Drop noise rows: references below the dashboard minimum coverage
        # threshold are typically incidental matches and add clutter.
        # The full per-reference list in the Alignment coverage tab is
        # not filtered so no data is lost.
        min_pct = self.config.get("filtering.dashboard_min_pct", 1.0)
        if "pct_ge_5x" in summary.columns:
            summary = summary.loc[summary["pct_ge_5x"] >= min_pct]
        if summary.empty:
            return pn.pane.Markdown(
                f"*No references with >= {min_pct:.0f}% bp covered at >= 5x.*",
                styles={"margin": "0 10px"},
            )
        cols = ["chrom", "species", "aliases", "length", "mean_depth", "pct_ge_5x", "pct_ge_10x"]
        if "aliases" not in summary.columns or summary["aliases"].eq("").all():
            cols = [c for c in cols if c != "aliases"]
        formatters = {"chrom": _ncbi_nuccore_link_formatter()}

        best_covered = summary.head(5)[cols].copy()
        best_covered_table = _compact_table(
            best_covered, name="Best-covered references", formatters=formatters
        )

        # Same per-reference frame, re-sorted by mean depth. The two
        # rankings often agree at the top, but a short reference with
        # very deep coverage can rank highly here while a longer one
        # with broad-but-shallow coverage wins on percent breadth.
        top_depth = (
            summary.sort_values("mean_depth", ascending=False, kind="mergesort")
            .head(5)[cols]
            .copy()
        )
        top_depth_table = _compact_table(
            top_depth, name="Highest mean depth references", formatters=formatters
        )

        return pn.Column(
            pn.pane.Markdown(
                "*Top 5 references by breadth (% bp >= 10x).*",
                styles={"margin": "0 10px 4px 10px", "font-size": "12px"},
            ),
            best_covered_table,
            pn.pane.Markdown(
                "### Highest mean depth references", styles={"margin": "10px 10px 0 10px"}
            ),
            pn.pane.Markdown(
                "*Same references re-ranked by mean depth - a short, "
                "deeply-covered reference can rank highly here while a "
                "longer one wins on breadth above.*",
                styles={"margin": "0 10px 4px 10px", "font-size": "12px"},
            ),
            top_depth_table,
            sizing_mode="stretch_width",
        )
