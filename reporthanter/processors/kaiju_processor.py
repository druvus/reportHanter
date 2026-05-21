"""
Kaiju data processor with improved error handling and configuration.
"""

import logging
from pathlib import Path

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
        """Process Kaiju TSV file into DataFrame."""
        df = pd.read_csv(file_path, sep="\t")
        return df.assign(percent=lambda x: x.percent / 100)

    def filter_data(
        self, data: pd.DataFrame, cutoff: float = 0.01, max_entries: int = 10
    ) -> tuple[pd.DataFrame, float]:
        """Filter Kaiju data by cutoff and max entries."""

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
        """Find Kaiju database files (.fmi, names.dmp, nodes.dmp)."""
        logger = logging.getLogger(__name__)
        db_path = Path(kaiju_db)

        if not db_path.exists() or not db_path.is_dir():
            raise DataProcessingError(f"Kaiju database directory not found: {kaiju_db}")

        files = list(db_path.iterdir())

        try:
            fmi_files = [f for f in files if f.suffix == ".fmi"]
            names_files = [f for f in files if f.name == "names.dmp"]
            nodes_files = [f for f in files if f.name == "nodes.dmp"]

            if not fmi_files:
                raise FileNotFoundError("No .fmi file found")
            if not names_files:
                raise FileNotFoundError("names.dmp not found")
            if not nodes_files:
                raise FileNotFoundError("nodes.dmp not found")

            fmi_file = str(fmi_files[0].resolve())
            names_file = str(names_files[0].resolve())
            nodes_file = str(nodes_files[0].resolve())

            logger.info(
                f"Found Kaiju database files: fmi={fmi_file}, names={names_file}, nodes={nodes_file}"
            )
            return fmi_file, names_file, nodes_file

        except FileNotFoundError as e:
            raise DataProcessingError(
                f"Required Kaiju database files not found in {kaiju_db}: {e}"
            ) from e


class KaijuPlotGenerator(BasePlotGenerator):
    """Generates Altair charts for Kaiju classification data."""

    DESCRIPTION = (
        "Bar chart of Kaiju protein-level taxonomic classifications. "
        "The horizontal axis shows the percentage of reads assigned to "
        "each taxon and the vertical axis lists taxa above the configured "
        "cutoff. The fraction of reads Kaiju left unclassified is "
        "reported in the axis title."
    )

    def _create_chart(self, data: pd.DataFrame, **kwargs) -> alt.Chart:
        """Create Kaiju classification bar chart.

        Mirrors the canonical Kraken bar styling: rounded corners,
        thin white stroke, nearest-point hover highlight, and direct
        percentage labels above 2 %. Colour is drawn from the
        ``mixed`` taxonomy palette in ``core.palettes`` so the
        Kraken / Kaiju / BLAST sections share a hue cycle.
        """
        title = kwargs.get("title", "Kaiju classification")
        unclassified_pct = kwargs.get("unclassified_pct", 0.0)

        x_axis = alt.X(
            "percent:Q",
            axis=alt.Axis(format="%"),
            title=f"Percent of reads ({unclassified_pct * 100:.1f}% not classified)",
            scale=alt.Scale(zero=True),
        )
        y_axis = alt.Y("taxon_name:N", sort="-x", title=None)
        tooltip = [
            alt.Tooltip("taxon_name:N", title="Taxon"),
            alt.Tooltip("reads:Q", title="Number of reads"),
            alt.Tooltip("percent:Q", title="Percentage", format=".2%"),
        ]

        hover = alt.selection_point(name="kaiju_hover", on="mouseover", empty=False, nearest=True)

        bars = (
            alt.Chart(data, title=title)
            .mark_bar(cornerRadius=3, stroke="white", strokeWidth=1, opacity=0.85)
            .encode(
                x=x_axis,
                y=y_axis,
                color=alt.Color(
                    "taxon_name:N",
                    title=None,
                    legend=None,
                    scale=alt.Scale(range=TAXONOMY_COLORS["mixed"]),
                ),
                opacity=alt.condition(hover, alt.value(1.0), alt.value(0.85)),
                tooltip=tooltip,
            )
            .add_params(hover)
        )

        labels = (
            alt.Chart(data)
            .mark_text(align="left", baseline="middle", dx=5, fontSize=10)
            .encode(
                x=x_axis,
                y=y_axis,
                text=alt.Text("percent:Q", format=".1%"),
                opacity=alt.condition(alt.datum.percent > 0.02, alt.value(1), alt.value(0)),
            )
        )

        return bars + labels
