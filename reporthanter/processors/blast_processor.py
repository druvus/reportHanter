"""
BLAST data processor with improved error handling and configuration.
"""

import subprocess
import tempfile
from pathlib import Path

import altair as alt
import pandas as pd

from ..core.base import BaseDataProcessor, BasePlotGenerator
from ..core.exceptions import DataProcessingError
from ..core.palettes import TAXONOMY_COLORS


class BlastProcessor(BaseDataProcessor):
    """Processes BLAST CSV files and runs BLASTN when needed."""

    def validate_input(self, file_path: str | Path) -> bool:
        """Validate BLAST CSV file format."""
        super().validate_input(file_path)

        try:
            # Check if it's a valid CSV
            test_df = pd.read_csv(file_path, nrows=5)
            self.logger.debug(f"BLAST CSV has {test_df.shape[1]} columns: {list(test_df.columns)}")
        except Exception as e:
            raise DataProcessingError(f"Invalid BLAST CSV format: {e}") from e

        return True

    def _process_file(self, file_path: str | Path) -> pd.DataFrame:
        """Process BLAST CSV file into DataFrame."""
        return pd.read_csv(file_path)

    def run_blastn(self, contigs_file: str | Path, database: str, threads: int = 4) -> pd.DataFrame:
        """Run BLASTN for contigs and return results DataFrame."""
        contigs_df = pd.read_csv(contigs_file)

        if contigs_df.empty:
            return contigs_df

        if not {"name", "sequence"}.issubset(contigs_df.columns):
            raise DataProcessingError("Contigs file must have 'name' and 'sequence' columns")

        matches = []

        with tempfile.NamedTemporaryFile(mode="w", suffix=".fasta", delete=False) as temp_file:
            temp_path = temp_file.name

            try:
                for _, contig in contigs_df.iterrows():
                    # Write contig to temporary file
                    temp_file.seek(0)
                    temp_file.truncate()
                    temp_file.write(f">{contig['name']}\n{contig['sequence']}\n")
                    temp_file.flush()

                    # Run BLASTN
                    command = [
                        "blastn",
                        "-num_threads",
                        str(threads),
                        "-task",
                        "megablast",
                        "-query",
                        temp_path,
                        "-db",
                        database,
                        "-max_target_seqs",
                        "1",
                        "-outfmt",
                        "6 stitle sacc pident slen",
                    ]

                    try:
                        result = subprocess.run(
                            command,
                            capture_output=True,
                            text=True,
                            check=True,
                            timeout=300,  # 5 minute timeout per query
                        )
                        matches.append(result.stdout.strip())
                    except subprocess.TimeoutExpired:
                        self.logger.warning(f"BLASTN timeout for contig {contig['name']}")
                        matches.append("")
                    except subprocess.CalledProcessError as e:
                        self.logger.warning(f"BLASTN failed for contig {contig['name']}: {e}")
                        matches.append("")

            finally:
                Path(temp_path).unlink(missing_ok=True)

        # Add matches to DataFrame
        result_df = contigs_df.assign(matches=matches)
        result_df = result_df.loc[result_df.matches != ""]

        if result_df.empty:
            return result_df

        # Parse BLAST output
        blast_columns = result_df.matches.str.split("\t", expand=True)
        if blast_columns.shape[1] >= 4:
            result_df[["match_name", "accession", "percent_identity", "sequence_len"]] = (
                blast_columns.iloc[:, :4]
            )
            # Clean up sequence_len (remove newlines)
            result_df["sequence_len"] = result_df["sequence_len"].str.split("\n").str[0]

        return result_df

    def top_matches_by_bp(self, data: pd.DataFrame, n: int = 5) -> pd.DataFrame:
        """Return the top ``n`` BLAST match_names by cumulative
        contig length.

        Reduces the per-contig BLAST frame to one row per
        ``match_name`` carrying the contig count and the cumulative
        ``read_len`` in bp, sorted by cumulative bp descending. Used
        by the Dashboard landing tab to surface the headline
        BLAST hits without redrawing the full bar chart.

        When ``read_len`` is absent or non-numeric on every row the
        helper falls back to a count-only ranking so the column is
        still populated.
        """
        if data.empty or "match_name" not in data.columns:
            return pd.DataFrame(columns=["match_name", "contigs", "cumulative_bp"])
        frame = data.copy()
        if "read_len" in frame.columns:
            frame["read_len"] = pd.to_numeric(frame["read_len"], errors="coerce")
        else:
            frame["read_len"] = pd.NA
        grouped = (
            frame.groupby("match_name", dropna=True)
            .agg(contigs=("match_name", "size"), cumulative_bp=("read_len", "sum"))
            .reset_index()
        )
        grouped["cumulative_bp"] = (
            pd.to_numeric(grouped["cumulative_bp"], errors="coerce").fillna(0).astype(int)
        )
        sort_col = "cumulative_bp" if grouped["cumulative_bp"].sum() > 0 else "contigs"
        return grouped.sort_values(sort_col, ascending=False).head(n).reset_index(drop=True)


class BlastPlotGenerator(BasePlotGenerator):
    """Generates Altair charts for BLAST results."""

    DESCRIPTION = (
        "Bar chart summarising BLASTN classification of de novo contigs. "
        "The horizontal axis shows the number of contigs assigned to each "
        "subject and the vertical axis lists subjects with at least one "
        "contig. Use the contig table below the chart for the full hit "
        "list and sequence retrieval."
    )

    def _create_chart(self, data: pd.DataFrame, **kwargs) -> alt.Chart:
        """Create BLAST results bar chart.

        Same rounded-corner / white-stroke / taxonomy-palette
        treatment used in the Kraken and Kaiju panes for visual
        consistency. When the table carries an ``assembler`` column
        the bars are colour-split by assembler so the reviewer can
        see whether MEGAHIT and metaSPAdes recovered comparable
        numbers of contigs per BLAST match.
        """
        title = kwargs.get("title", "BLASTN of Contigs")

        if data.empty or "match_name" not in data.columns:
            return self._empty_chart(title="No classified contigs")

        multi_assembler = "assembler" in data.columns and data["assembler"].nunique() > 1

        # Keep only the columns the chart references so neither the
        # raw BLAST stitle (``matches``) nor any ``*_raw`` audit
        # column from the upstream canonicaliser leaks into the
        # Vega data embed.
        chart_cols = [c for c in ("match_name", "assembler") if c in data.columns]
        chart_data = data[chart_cols].copy()

        chart = (
            alt.Chart(chart_data, title=title)
            .mark_bar(cornerRadius=3, stroke="white", strokeWidth=1)
            .properties(width="container", height=alt.Step(22))
        )

        if multi_assembler:
            # Legend-bound selection so reviewers can toggle each
            # assembler's contribution by clicking the legend in the
            # saved static HTML (no Panel server needed).
            select_asm = alt.selection_point(fields=["assembler"], bind="legend")
            chart = chart.encode(
                alt.X(
                    "count():Q",
                    title="Number of contigs",
                    axis=alt.Axis(format="d", tickMinStep=1),
                    stack="zero",
                ),
                alt.Y("match_name:N", sort="-x", title=None),
                color=alt.Color(
                    "assembler:N",
                    title="Assembler",
                    legend=alt.Legend(title="Assembler"),
                    scale=alt.Scale(range=TAXONOMY_COLORS["mixed"]),
                ),
                opacity=alt.condition(select_asm, alt.value(1.0), alt.value(0.15)),
                tooltip=[
                    alt.Tooltip("match_name:N", title="Match"),
                    alt.Tooltip("assembler:N", title="Assembler"),
                    alt.Tooltip("count():Q", title="Number of contigs"),
                ],
            ).add_params(select_asm)
            return chart

        return chart.encode(
            alt.X(
                "count():Q",
                title="Number of contigs",
                axis=alt.Axis(format="d", tickMinStep=1),
                stack="zero",
            ),
            alt.Y("match_name:N", sort="-x", title=None),
            color=alt.Color(
                "match_name:N",
                title=None,
                legend=None,
                scale=alt.Scale(range=TAXONOMY_COLORS["mixed"]),
            ),
            tooltip=[
                alt.Tooltip("match_name:N", title="Match"),
                alt.Tooltip("count(match_name):Q", title="Number of contigs"),
            ],
        )

    def create_bp_chart(self, data: pd.DataFrame, **kwargs) -> alt.Chart:
        """Companion to ``_create_chart`` that sums contig length
        (``read_len``) per BLAST match.

        The count chart treats each contig equally; for a clinical
        reviewer looking at coverage breadth the *cumulative base
        pairs* assigned to a match is the more relevant measure.
        Three short contigs of 1 kb each contribute less evidence
        for a 30 kb herpesvirus genome than a single 25 kb contig.

        Falls back to an empty chart when neither ``match_name``
        nor ``read_len`` is present (e.g. when no contigs were
        classified).
        """
        title = kwargs.get("title", "Cumulative bp per BLAST match")

        if data.empty or "match_name" not in data.columns or "read_len" not in data.columns:
            return self._empty_chart(title="No classified contigs")

        multi_assembler = "assembler" in data.columns and data["assembler"].nunique() > 1

        # Keep only the columns the chart references (match_name,
        # assembler, read_len) so neither the raw BLAST stitle
        # (``matches``) nor any ``*_raw`` audit column leaks into
        # the Vega data embed. Normalise read_len to int for safe
        # `sum()` aggregation in Vega-Lite.
        keep = [c for c in ("match_name", "assembler", "read_len") if c in data.columns]
        chart_data = data[keep].copy()
        chart_data["read_len"] = pd.to_numeric(chart_data["read_len"], errors="coerce")
        chart_data = chart_data.dropna(subset=["read_len"])
        chart_data["read_len"] = chart_data["read_len"].astype(int)

        # Step-based height: Vega-Lite allocates 22px per category so
        # the chart grows with the number of matches. A fixed height
        # caused two failure modes: long lists got compressed into
        # unreadable bars, and the chart's intrinsic height could
        # exceed the surrounding pane and clip the x-axis at the
        # bottom. Pairing alt.Step(...) with a stretch_width Vega pane
        # that has no fixed height lets the chart drive its own
        # vertical extent and keeps the axis visible.
        chart = (
            alt.Chart(chart_data, title=title)
            .mark_bar(cornerRadius=3, stroke="white", strokeWidth=1)
            .properties(width="container", height=alt.Step(22))
        )

        # Clean bp bar chart, no overlaid count labels. The
        # contig-count view is rendered as a separate chart panel
        # in `ContigClassificationSection` so the two metrics
        # have distinct titles and cannot be confused.
        if multi_assembler:
            select_asm = alt.selection_point(fields=["assembler"], bind="legend")
            return chart.encode(
                alt.X(
                    "sum(read_len):Q",
                    title="Cumulative contig length (bp)",
                    axis=alt.Axis(format=","),
                    stack="zero",
                ),
                alt.Y("match_name:N", sort="-x", title=None),
                color=alt.Color(
                    "assembler:N",
                    title="Assembler",
                    legend=alt.Legend(title="Assembler"),
                    scale=alt.Scale(range=TAXONOMY_COLORS["mixed"]),
                ),
                opacity=alt.condition(select_asm, alt.value(1.0), alt.value(0.15)),
                tooltip=[
                    alt.Tooltip("match_name:N", title="Match"),
                    alt.Tooltip("assembler:N", title="Assembler"),
                    alt.Tooltip(
                        "sum(read_len):Q",
                        title="Cumulative bp",
                        format=",",
                    ),
                ],
            ).add_params(select_asm)

        return chart.encode(
            alt.X(
                "sum(read_len):Q",
                title="Cumulative contig length (bp)",
                axis=alt.Axis(format=","),
                stack="zero",
            ),
            alt.Y("match_name:N", sort="-x", title=None),
            color=alt.Color(
                "match_name:N",
                title=None,
                legend=None,
                scale=alt.Scale(range=TAXONOMY_COLORS["mixed"]),
            ),
            tooltip=[
                alt.Tooltip("match_name:N", title="Match"),
                alt.Tooltip("sum(read_len):Q", title="Cumulative bp", format=","),
            ],
        )
