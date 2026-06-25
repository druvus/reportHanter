"""
Flagstat data processor with improved error handling and configuration.
"""

import re
from pathlib import Path

import altair as alt
import pandas as pd
import panel as pn

from ..core.base import BaseDataProcessor, BasePlotGenerator
from ..core.exceptions import DataProcessingError
from ..core.palettes import QUALITY_GRADIENTS


class FlagstatProcessor(BaseDataProcessor):
    """Processes BWA flagstat files into alignment statistics."""

    def validate_input(self, file_path: str | Path) -> bool:
        """Validate flagstat file format."""
        super().validate_input(file_path)

        try:
            with open(file_path) as f:
                content = f.read()

            # Check for expected patterns
            if "paired in sequencing" not in content:
                raise DataProcessingError("File doesn't appear to be a BWA flagstat output")

        except Exception as e:
            raise DataProcessingError(f"Invalid flagstat file: {e}") from e

        return True

    def _process_file(self, file_path: str | Path) -> pd.DataFrame:
        """Process flagstat file into DataFrame with alignment statistics."""
        total_reads, percent_mapped = self._parse_flagstat(file_path)

        # Create a simple DataFrame with the statistics
        return pd.DataFrame(
            {
                "metric": ["total_reads", "percent_mapped", "reads_mapped", "reads_unmapped"],
                "value": [
                    total_reads,
                    percent_mapped,
                    int(total_reads * percent_mapped / 100),
                    int(total_reads * (100 - percent_mapped) / 100),
                ],
            }
        )

    def _parse_flagstat(self, file_path: str | Path) -> tuple[int, float]:
        """Parse BWA flagstat file to extract reads and mapping percentage.

        Raises :exc:`~reporthanter.core.exceptions.DataProcessingError`
        when either expected pattern is absent, naming the file so the
        caller can diagnose format changes without inspecting the
        exception chain.
        """
        pattern_total = r"(\d+) \+ \d+ paired in sequencing"
        pattern_mapped = r"(\d+) \+ \d+ with itself and mate mapped"

        with open(file_path) as f:
            content = f.read()

        total_matches = re.findall(pattern_total, content)
        mapped_matches = re.findall(pattern_mapped, content)

        if not total_matches:
            raise DataProcessingError(
                f"Could not find 'paired in sequencing' line in flagstat file: {file_path}"
            )
        if not mapped_matches:
            raise DataProcessingError(
                f"Could not find 'with itself and mate mapped' line in flagstat file: {file_path}"
            )

        try:
            total_reads = int(total_matches[0])
            total_mapped = int(mapped_matches[0])
        except ValueError as e:
            raise DataProcessingError(
                f"Could not parse integer from flagstat file {file_path}: {e}"
            ) from e

        percent_mapped = 0.0 if total_reads == 0 else total_mapped / total_reads * 100
        # Clamp to [0, 100]: some samtools outputs count supplementary /
        # secondary alignments so "with itself and mate mapped" exceeds
        # "paired in sequencing", which would otherwise yield a >100%
        # mapped tile and a negative "unaligned" segment in the chart.
        percent_mapped = max(0.0, min(100.0, percent_mapped))

        return total_reads, percent_mapped

    def create_alignment_chart(self, data: pd.DataFrame, species: str = "Host") -> pn.pane.Vega:
        """Build the normalised stacked bar pane for one flagstat.

        The headline counts that used to be rendered as h3 markdown
        beside this chart are already in the KPI tile strip above the
        section, so this helper now returns only the chart.
        """
        plot_generator = FlagstatPlotGenerator()
        chart = plot_generator.generate_plot(
            data, species=species, title=f"Reads aligned to {species}"
        )

        return pn.pane.Vega(
            chart,
            sizing_mode="stretch_width",
            height=70,
            name=f"{species} Alignment Plot",
        )


class FlagstatPlotGenerator(BasePlotGenerator):
    """Generates Altair charts for alignment statistics."""

    # The chart height is set in _create_chart (a small single-bar pane);
    # the base-class height=400 stamp must not override it.
    PRESERVE_CHART_HEIGHT = True

    def _create_chart(self, data: pd.DataFrame, **kwargs: object) -> alt.Chart:
        """Create alignment statistics normalised stacked bar chart.

        The two-segment bar uses the head and tail of the
        ``good_to_bad`` quality gradient so the unaligned (host-free)
        fraction reads as green and the aligned (host-contamination)
        fraction reads as red. Consistent with the palette used
        across the rest of the report.
        """
        species = kwargs.get("species", "Host")
        title = kwargs.get("title", f"Reads aligned to {species}")

        stats_dict = dict(zip(data["metric"], data["value"], strict=False))
        reads_mapped = stats_dict.get("reads_mapped", 0)
        reads_unmapped = stats_dict.get("reads_unmapped", 0)

        viz_data = pd.DataFrame(
            {
                "amount": [reads_unmapped, reads_mapped],
                "type": ["unaligned", "aligned"],
            }
        )

        good_bad = QUALITY_GRADIENTS["good_to_bad"]
        return (
            alt.Chart(viz_data, title=title)
            .mark_bar(cornerRadius=3, stroke="white", strokeWidth=1)
            .encode(
                x=alt.X(
                    "sum(amount)",
                    stack="normalize",
                    axis=alt.Axis(format="%"),
                    title=None,
                ),
                color=alt.Color(
                    "type:N",
                    scale=alt.Scale(
                        domain=["unaligned", "aligned"],
                        range=[good_bad[0], good_bad[-1]],
                    ),
                    title=None,
                ),
                tooltip=[
                    alt.Tooltip("amount:Q", title="Number of reads"),
                    alt.Tooltip("type:N", title="Type"),
                ],
            )
            .properties(width="container", height=40)
        )
