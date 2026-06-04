"""Coverage processor and plot generator.

Reads mosdepth ``regions.bed.gz`` output (a windowed mean-depth BED
file produced by ``mosdepth --by N``) and renders an interactive
per-reference coverage chart for the report.

The input is a gzip-compressed BED with four columns:

    chrom  start  end  mean_depth

One row per window. References with no aligned reads do not appear in
the file at all and are simply omitted from the chart.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import altair as alt
import pandas as pd

from ..core.base import BaseDataProcessor, BasePlotGenerator
from ..core.exceptions import DataProcessingError


class CoverageProcessor(BaseDataProcessor):
    """Parses a mosdepth regions BED into a tidy DataFrame.

    Returned columns: ``chrom``, ``start``, ``end``, ``mid``, ``depth``.
    ``mid`` is the window midpoint, included so the plot's x-axis maps
    naturally to a single point per window rather than a range.
    """

    REQUIRED_COLUMNS: tuple[str, ...] = ("chrom", "start", "end", "depth")

    def _process_file(self, file_path: str | Path) -> pd.DataFrame:
        path = Path(file_path)
        try:
            df = pd.read_csv(
                path,
                sep="\t",
                header=None,
                names=list(self.REQUIRED_COLUMNS),
                compression="infer",
            )
        except Exception as e:
            raise DataProcessingError(f"Failed to parse mosdepth regions file {path}: {e}") from e

        if df.empty:
            return df.assign(mid=pd.Series(dtype="float64"))

        df["mid"] = (df["start"] + df["end"]) / 2.0
        return df


class CoveragePlotGenerator(BasePlotGenerator):
    """Renders an interactive coverage chart per reference."""

    DESCRIPTION = (
        "Interactive coverage trace per reference. The horizontal axis "
        "is the reference position in base pairs and the vertical axis "
        "is the mean read depth within each mosdepth window. Hover any "
        "point to read the exact window coordinates and depth."
    )

    def _create_chart(self, data: pd.DataFrame, **kwargs: Any) -> alt.Chart:
        chrom = kwargs.get("chrom", "reference")
        title = kwargs.get("title", f"Coverage: {chrom}")

        tooltip = [
            alt.Tooltip("chrom:N", title="Reference"),
            alt.Tooltip("start:Q", title="Window start"),
            alt.Tooltip("end:Q", title="Window end"),
            alt.Tooltip("depth:Q", title="Mean depth", format=".2f"),
        ]
        x_enc = alt.X("mid:Q", title="Reference position (bp)")
        y_enc = alt.Y("depth:Q", title="Mean depth")

        # Two cooperating layers (Altair 6 idiom):
        #   - area + line render the trace.
        #   - a transparent point layer carries a nearest-point hover
        #     selection so the tooltip and rule track the cursor along
        #     the whole x-axis, not only at exact window midpoints.
        nearest = alt.selection_point(
            name="cov_hover",
            nearest=True,
            on="mouseover",
            fields=["mid"],
            empty=False,
        )

        area = alt.Chart(data).mark_area(opacity=0.4).encode(x=x_enc, y=y_enc)
        line = alt.Chart(data).mark_line().encode(x=x_enc, y=y_enc)

        hover_points = (
            alt.Chart(data)
            .mark_point(opacity=0)
            .encode(x=x_enc, y=y_enc, tooltip=tooltip)
            .add_params(nearest)
        )
        rule = alt.Chart(data).mark_rule(color="gray").encode(x=x_enc).transform_filter(nearest)

        return alt.layer(area, line, hover_points, rule, title=title)  # type: ignore[return-value]
