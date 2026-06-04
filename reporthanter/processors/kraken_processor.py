"""
Kraken data processor with improved error handling and configuration.
"""

from pathlib import Path
from typing import Any

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
        """Filter Kraken data by taxonomy level and other criteria.

        Returns a tuple of (filtered_df, unclassified_pct).  When
        ``data`` is empty or contains no row with ``domain ==
        'unclassified'``, ``unclassified_pct`` is 0.0 and
        ``filtered_df`` is an empty DataFrame; no ``IndexError`` is
        raised.

        .. note::
            Kraken files are required to be non-empty (validated by
            :func:`~reporthanter.core.validation.validate_report_inputs`).
            The empty-input guard here is a belt-and-braces measure for
            callers that use the processor directly.

        .. rubric:: Threshold precedence

        The method-signature defaults (``level="species"``,
        ``cutoff=0.001``, ``max_entries=10``, ``virus_only=True``)
        match the values in ``DefaultConfig.DEFAULT_CONFIG["filtering"]["kraken"]``
        and are used only when this method is called without a config
        object.  The normal report pipeline always passes the config
        dict as ``**kwargs``, so the config is the single source of
        truth in production runs.  If you change a threshold, update
        **both** the config and the method signature.
        """
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

    # alt.Step-based per-bar height: preserve the chart's own height.
    PRESERVE_CHART_HEIGHT = True

    DESCRIPTION = (
        "Bar chart of Kraken2 taxonomic classifications. The horizontal "
        "axis shows the percentage of reads assigned to each taxon and "
        "the vertical axis lists taxa above the configured cutoff. The "
        "fraction of reads Kraken2 left unclassified is reported in the "
        "axis title."
    )

    def _create_chart(self, data: pd.DataFrame, **kwargs: Any) -> alt.Chart:
        """Create Kraken classification bar chart.

        Two visual choices for a scientific report:

        - rounded bar corners with a thin white stroke so adjacent
          bars read as distinct categories;
        - colour drawn from the categorical ``mixed`` palette in
          ``core.palettes`` so the same hue cycles across the
          Kraken, Kaiju and BLAST sections of the report.

        ``alt.Step(22)`` gives each bar a fixed 22 px height so
        the styling matches the BLAST and Host alignment charts;
        the chart's total height then scales with the number of
        bars rather than being fixed at 400 px.

        Exact percentages and read counts are reported in the hover
        tooltip; an earlier iteration with an inline ``mark_text``
        overlay rendered blank when wrapped in Panel's
        ColumnDataSource-backed Vega embed.
        """
        title = kwargs.get("title", "Kraken classification")
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
                ),
                alt.Y("name:N", sort="-x", title=None),
                alt.Color(
                    "name:N",
                    title=None,
                    legend=None,
                    scale=alt.Scale(range=TAXONOMY_COLORS["mixed"]),
                ),
                tooltip=[
                    alt.Tooltip("domain:N"),
                    alt.Tooltip("name:N", title="Species"),
                    alt.Tooltip("count_clades:Q", title="Number of reads"),
                    alt.Tooltip("percent:Q", title="Percentage", format=".2%"),
                ],
            )
        )
