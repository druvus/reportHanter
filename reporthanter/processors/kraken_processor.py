"""
Kraken data processor with improved error handling and configuration.
"""

from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd

from ..core.base import BaseDataProcessor, BasePlotGenerator
from ..core.exceptions import DataProcessingError
from ..core.palettes import TAXONOMY_COLORS


class KrakenProcessor(BaseDataProcessor):
    """Processes Kraken TSV files into standardized DataFrames."""

    TAXONOMY_LEVELS = {
        "domain": "D",
        "phylum": "P",
        "class": "K",
        "order": "O",
        "family": "F",
        "genus": "G",
        "species": "S",
    }

    def validate_input(self, file_path: str | Path) -> bool:
        """Validate Kraken file format."""
        super().validate_input(file_path)

        # Check if it looks like a Kraken file
        try:
            test_df = pd.read_csv(file_path, sep="\t", nrows=5, header=None)
            if test_df.shape[1] != 6:
                raise DataProcessingError(
                    f"Expected 6 columns in Kraken file, got {test_df.shape[1]}"
                )
        except Exception as e:
            raise DataProcessingError(f"Invalid Kraken file format: {e}") from e

        return True

    def _process_file(self, file_path: str | Path) -> pd.DataFrame:
        """Process Kraken TSV file into DataFrame.

        The ``domain`` column is carried down from the nearest D/U/R/R1
        parent. Including R1 lets the viral-only Kraken2 databases
        (e.g. ``k2_viral_*``) tag Viruses correctly — those DBs place
        Viruses at ``tax_lvl='R1'`` because they have no sibling
        superkingdom requiring a domain level. The standard pluspf DB
        is unaffected because its only R1 row ("cellular organisms")
        is immediately overridden by the next D row (Bacteria).
        """
        df = pd.read_csv(
            file_path,
            sep="\t",
            header=None,
            names=["percent", "count_clades", "count", "tax_lvl", "taxonomy_id", "name"],
        )

        return (
            df.assign(name=lambda x: x.name.str.strip())
            .assign(
                domain=lambda x: np.select(
                    [x.tax_lvl.isin(["D", "U", "R", "R1"])], [x.name], default=pd.NA
                )
            )
            .ffill()
            .assign(percent=lambda x: x.percent / 100)
        )

    def filter_data(
        self,
        data: pd.DataFrame,
        level: str = "species",
        cutoff: float = 0.001,
        max_entries: int = 10,
        virus_only: bool = True,
    ) -> tuple[pd.DataFrame, float]:
        """Filter Kraken data by taxonomy level and other criteria."""

        if level not in self.TAXONOMY_LEVELS:
            raise ValueError(
                f"Invalid taxonomy level: {level}. Must be one of {list(self.TAXONOMY_LEVELS.keys())}"
            )

        # Get unclassified percentage
        unclassified_rows = data.loc[data.domain == "unclassified"]
        unclassified_pct = unclassified_rows.percent.iloc[0] if len(unclassified_rows) > 0 else 0.0

        # Filter by taxonomy level and cutoff
        filtered_df = (
            data.loc[data.tax_lvl == self.TAXONOMY_LEVELS[level]]
            .loc[data.percent > cutoff]
            .sort_values("percent", ascending=False)
        )

        # Apply virus filter if requested
        if virus_only:
            filtered_df = filtered_df.loc[filtered_df.domain == "Viruses"]

        return filtered_df.head(max_entries), unclassified_pct


class KrakenPlotGenerator(BasePlotGenerator):
    """Generates Altair charts for Kraken classification data."""

    DESCRIPTION = (
        "Bar chart of Kraken2 taxonomic classifications. The horizontal "
        "axis shows the percentage of reads assigned to each taxon and "
        "the vertical axis lists taxa above the configured cutoff. The "
        "fraction of reads Kraken2 left unclassified is reported in the "
        "axis title."
    )

    def _create_chart(self, data: pd.DataFrame, **kwargs) -> alt.Chart:
        """Create Kraken classification bar chart.

        Three deliberate visual choices for a scientific report:

        - rounded bar corners with a thin white stroke so adjacent
          bars read as distinct categories rather than as a stacked
          fill;
        - hover highlighting via a ``selection_point`` parameter so
          the active row is visually emphasised without changing
          the underlying layout;
        - direct percentage labels via a ``mark_text`` overlay,
          shown only when the bar exceeds 2 % of reads to avoid
          clutter on noise-dominated samples.

        Colour is drawn from the categorical ``mixed`` palette in
        ``core.palettes`` so the same hue cycles across the Kraken,
        Kaiju and BLAST sections of the report.
        """
        title = kwargs.get("title", "Kraken classification")
        unclassified_pct = kwargs.get("unclassified_pct", 0.0)

        x_axis = alt.X(
            "percent:Q",
            axis=alt.Axis(format="%"),
            title=f"Percent of reads ({unclassified_pct * 100:.1f}% not classified)",
        )
        y_axis = alt.Y("name:N", sort="-x", title=None)
        tooltip = [
            alt.Tooltip("domain:N"),
            alt.Tooltip("name:N", title="Species"),
            alt.Tooltip("count_clades:Q", title="Number of reads"),
            alt.Tooltip("percent:Q", title="Percentage", format=".2%"),
        ]

        hover = alt.selection_point(name="kraken_hover", on="mouseover", empty=False, nearest=True)

        bars = (
            alt.Chart(data, title=title)
            .mark_bar(cornerRadius=3, stroke="white", strokeWidth=1, opacity=0.85)
            .encode(
                x=x_axis,
                y=y_axis,
                color=alt.Color(
                    "name:N",
                    title=None,
                    legend=None,
                    scale=alt.Scale(range=TAXONOMY_COLORS["mixed"]),
                ),
                opacity=alt.condition(hover, alt.value(1.0), alt.value(0.85)),
                tooltip=tooltip,
            )
            .add_params(hover)
        )

        # Inline percentage labels — only above 2 % so low-noise
        # bars do not crowd the y-axis category labels.
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
