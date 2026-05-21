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

        multi_assembler = (
            "assembler" in data.columns and data["assembler"].nunique() > 1
        )

        chart = alt.Chart(data, title=title).mark_bar(
            cornerRadius=3, stroke="white", strokeWidth=1
        )

        if multi_assembler:
            # Legend-bound selection so reviewers can toggle each
            # assembler's contribution by clicking the legend in the
            # saved static HTML (no Panel server needed).
            select_asm = alt.selection_point(
                fields=["assembler"], bind="legend"
            )
            chart = (
                chart.encode(
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
                )
                .add_params(select_asm)
            )
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
