"""
Base classes with common functionality for reportHanter.
"""

import logging
from pathlib import Path
from typing import Any

import altair as alt
import pandas as pd

from .exceptions import DataProcessingError, FileValidationError, PlotGenerationError
from .interfaces import DataProcessor, PlotGenerator


class BaseDataProcessor(DataProcessor):
    """Base implementation for data processors with common functionality."""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_input(self, file_path: str | Path) -> bool:
        """Validate that the input file exists and is readable."""
        path = Path(file_path)
        if not path.exists():
            raise FileValidationError(f"File does not exist: {file_path}")
        if not path.is_file():
            raise FileValidationError(f"Path is not a file: {file_path}")
        if not path.stat().st_size > 0:
            raise FileValidationError(f"File is empty: {file_path}")
        return True

    def process(self, file_path: str | Path) -> pd.DataFrame:
        """Process the input file with error handling."""
        self.validate_input(file_path)
        try:
            self.logger.info(f"Processing file: {file_path}")
            result = self._process_file(file_path)
            self.logger.info(f"Successfully processed {len(result)} records")
            return result
        except Exception as e:
            self.logger.error(f"Failed to process file {file_path}: {e}")
            raise DataProcessingError(f"Failed to process {file_path}: {e}") from e

    def _process_file(self, file_path: str | Path) -> pd.DataFrame:
        """Override this method in subclasses."""
        raise NotImplementedError("Subclasses must implement _process_file")


class BasePlotGenerator(PlotGenerator):
    """Base implementation for plot generators with common styling.

    Subclasses that use ``alt.Step``-based per-bar heights (Kraken, Kaiju,
    BLAST, Flagstat) should set ``PRESERVE_CHART_HEIGHT = True`` so that
    ``_apply_styling`` skips the fixed ``height=400`` stamp and lets the
    chart's own intrinsic height drive the vertical extent.
    """

    # Subclasses set a short, plain description of what the chart shows.
    # Emitted as the Vega-Lite ``description`` property so assistive
    # technology has a textual fallback for the rendered chart.
    DESCRIPTION: str = ""

    # Set to True in subclasses whose charts use alt.Step-based heights.
    # When True, _apply_styling omits the height stamp so the chart's own
    # step-based height is preserved.
    PRESERVE_CHART_HEIGHT: bool = False

    # Panel Vega pane sizing mode.  Use ``"stretch_width"`` (not
    # ``"stretch_both"``) for all chart panes: ``"stretch_both"`` causes
    # Panel to force the pane to fill the surrounding container's full
    # height, which Vega then stretches to fill — turning compact
    # alt.Step(22) bars into 60–100 px blocks.  ``"stretch_width"`` lets
    # the chart's own intrinsic height (set by alt.Step or a fixed
    # ``height=...``) drive the vertical extent while still filling the
    # available width.  Sections should obtain this value via the
    # generator attribute rather than hardcoding the string.
    CHART_SIZING_MODE: str = "stretch_width"

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)

    def generate_plot(self, data: pd.DataFrame, **kwargs: Any) -> alt.Chart:
        """Generate plot with error handling and common styling."""
        try:
            if data.empty:
                return self._empty_chart(**kwargs)

            chart = self._create_chart(data, **kwargs)
            chart = self._apply_styling(chart)
            description = kwargs.get("description") or self.DESCRIPTION
            if description:
                chart = chart.properties(description=description)
            return chart

        except Exception as e:
            self.logger.error(f"Failed to generate plot: {e}")
            raise PlotGenerationError(f"Failed to generate plot: {e}") from e

    def _create_chart(self, data: pd.DataFrame, **kwargs: Any) -> alt.Chart:
        """Override this method in subclasses."""
        raise NotImplementedError("Subclasses must implement _create_chart")

    def _empty_chart(self, title: str = "No Data Available", **kwargs: Any) -> alt.Chart:
        """Create a placeholder chart for empty data."""
        return (
            alt.Chart(pd.DataFrame({"message": [title]}))
            .mark_text(fontSize=20, color="gray")
            .encode(text="message:N")
            .properties(
                title=title,
                width=self.config.get("width", "container"),
                height=self.config.get("height", 200),
            )
        )

    def _apply_styling(self, chart: alt.Chart) -> alt.Chart:
        """Apply common styling to charts.

        When ``PRESERVE_CHART_HEIGHT`` is ``True`` on the subclass the
        ``height`` stamp is omitted so that ``alt.Step``-based per-bar
        heights set in ``_create_chart`` are not overridden.  The
        ``resolve_scale`` call is always applied.
        """
        if self.PRESERVE_CHART_HEIGHT:
            return chart.resolve_scale(color="independent")
        return chart.properties(
            width=self.config.get("width", "container"), height=self.config.get("height", 400)
        ).resolve_scale(color="independent")
