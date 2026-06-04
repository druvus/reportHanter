"""
Kaiju data processor with improved error handling and configuration.
"""

import logging
from pathlib import Path
from typing import Any

import altair as alt
import pandas as pd

from ..core.base import BaseDataProcessor, BasePlotGenerator
from ..core.exceptions import DataProcessingError
from ..core.palettes import TAXONOMY_COLORS


class KaijuProcessor(BaseDataProcessor):
    """Processes Kaiju TSV files into standardized DataFrames."""

    def validate_input(self, file_path: str | Path) -> bool:
        """Validate Kaiju file format."""
        super().validate_input(file_path)

        # Check if it looks like a Kaiju file
        try:
            test_df = pd.read_csv(file_path, sep="\t", nrows=5)
            required_columns = {"percent", "taxon_name"}
            if not required_columns.issubset(test_df.columns):
                missing = required_columns - set(test_df.columns)
                raise DataProcessingError(f"Missing required columns in Kaiju file: {missing}")
        except Exception as e:
            raise DataProcessingError(f"Invalid Kaiju file format: {e}") from e

        return True

    def _process_file(self, file_path: str | Path) -> pd.DataFrame:
        """Process Kaiju TSV file into DataFrame.

        Drops any ``*_raw`` audit columns the upstream pipeline keeps
        alongside the canonicalised ``taxon_name`` so they cannot
        leak through the Vega data embed into the rendered HTML.
        """
        df = pd.read_csv(file_path, sep="\t")
        drop = [c for c in df.columns if c.endswith("_raw")]
        if drop:
            df = df.drop(columns=drop)
        return df.assign(percent=lambda x: x.percent / 100)

    def filter_data(
        self, data: pd.DataFrame, cutoff: float = 0.01, max_entries: int = 10
    ) -> tuple[pd.DataFrame, float]:
        """Filter Kaiju data by cutoff and max entries.

        Returns a tuple of (filtered_df, unclassified_pct).  When
        ``data`` is empty or contains no 'unclassified' row,
        ``unclassified_pct`` is 0.0 and ``filtered_df`` is an empty
        DataFrame; no ``IndexError`` is raised.

        .. note::
            Kaiju tables are required to be non-empty (validated by
            :func:`~reporthanter.core.validation.validate_report_inputs`).
            The empty-input guard here is a belt-and-braces measure for
            callers that use the processor directly.

        .. rubric:: Threshold precedence

        The method-signature defaults (``cutoff=0.01``, ``max_entries=10``)
        match the values in ``DefaultConfig.DEFAULT_CONFIG["filtering"]["kaiju"]``
        and are used only when this method is called without a config
        object.  The normal report pipeline always passes the config
        dict as ``**kwargs``, so the config is the single source of
        truth in production runs.  If you change a threshold, update
        **both** the config and the method signature.
        """
        # Get unclassified percentage
        unclassified_rows = data.loc[data.taxon_name == "unclassified"]
        unclassified_pct = unclassified_rows.percent.iloc[0] if len(unclassified_rows) > 0 else 0.0

        # Filter out unclassified entries and apply cutoff
        filtered_df = (
            data.drop(columns=["file"], errors="ignore")
            .sort_values("percent", ascending=False)
            .loc[data.taxon_name != "unclassified"]
            .loc[data.percent > cutoff]
            .head(max_entries)
        )

        return filtered_df, unclassified_pct

    @staticmethod
    def find_database_files(kaiju_db: str | Path) -> tuple[str, str, str]:
        """Find Kaiju database files (.fmi, names.dmp, nodes.dmp).

        Raises :exc:`~reporthanter.core.exceptions.DataProcessingError`
        when the directory does not exist or any of the three required
        database files are absent.  Each error message names the
        directory that was searched so the caller can produce a
        diagnostic without having to catch and re-inspect the
        exception.
        """
        logger = logging.getLogger(__name__)
        db_path = Path(kaiju_db)

        if not db_path.exists() or not db_path.is_dir():
            raise DataProcessingError(f"Kaiju database directory not found: {kaiju_db}")

        files = list(db_path.iterdir())

        fmi_files = [f for f in files if f.suffix == ".fmi"]
        names_files = [f for f in files if f.name == "names.dmp"]
        nodes_files = [f for f in files if f.name == "nodes.dmp"]

        if not fmi_files:
            raise DataProcessingError(f"No .fmi database file found in {kaiju_db}")
        if not names_files:
            raise DataProcessingError(f"names.dmp not found in {kaiju_db}")
        if not nodes_files:
            raise DataProcessingError(f"nodes.dmp not found in {kaiju_db}")

        fmi_file = str(fmi_files[0].resolve())
        names_file = str(names_files[0].resolve())
        nodes_file = str(nodes_files[0].resolve())

        logger.info(
            f"Found Kaiju database files: fmi={fmi_file}, names={names_file}, nodes={nodes_file}"
        )
        return fmi_file, names_file, nodes_file


class KaijuPlotGenerator(BasePlotGenerator):
    """Generates Altair charts for Kaiju classification data."""

    # alt.Step-based per-bar height: preserve the chart's own height.
    PRESERVE_CHART_HEIGHT = True

    DESCRIPTION = (
        "Bar chart of Kaiju protein-level taxonomic classifications. "
        "The horizontal axis shows the percentage of reads assigned to "
        "each taxon and the vertical axis lists taxa above the configured "
        "cutoff. The fraction of reads Kaiju left unclassified is "
        "reported in the axis title."
    )

    def _create_chart(self, data: pd.DataFrame, **kwargs: Any) -> alt.Chart:
        """Create Kaiju classification bar chart.

        Mirrors the canonical Kraken bar styling: rounded corners,
        thin white stroke, and the ``mixed`` taxonomy palette from
        ``core.palettes``. ``alt.Step(22)`` gives each bar a fixed
        22 px height to match the BLAST and Host alignment charts.
        Hover tooltips report the exact taxon name, read count and
        percentage; a previous iteration drew inline percentage
        labels via a layered ``mark_text`` overlay, but the layered
        chart did not reconcile cleanly with Panel's
        ColumnDataSource-backed Vega embed.
        """
        title = kwargs.get("title", "Kaiju classification")
        unclassified_pct = kwargs.get("unclassified_pct", 0.0)

        return (
            alt.Chart(data, title=title)
            .mark_bar(cornerRadius=3, stroke="white", strokeWidth=1)
            .properties(width="container", height=alt.Step(self.config.get("bar_step_px", 22)))
            .encode(
                alt.X(
                    "percent:Q",
                    axis=alt.Axis(format="%"),
                    title=f"Percent of reads ({unclassified_pct * 100:.1f}% not classified)",
                    scale=alt.Scale(zero=True),
                ),
                alt.Y("taxon_name:N", sort="-x", title=None),
                alt.Color(
                    "taxon_name:N",
                    title=None,
                    legend=None,
                    scale=alt.Scale(range=TAXONOMY_COLORS["mixed"]),
                ),
                tooltip=[
                    alt.Tooltip("taxon_name:N", title="Taxon"),
                    alt.Tooltip("reads:Q", title="Number of reads"),
                    alt.Tooltip("percent:Q", title="Percentage", format=".2%"),
                ],
            )
        )
