"""QUAST report processor.

Parses a QUAST ``report.tsv`` (two-column TSV: metric name, value) and
exposes a small key/value table for the report. The interactive Altair
charts in the rest of the report do not apply here — QUAST output is
a fixed set of summary metrics.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import panel as pn

from ..core.base import BaseDataProcessor
from ..core.exceptions import DataProcessingError


class QuastProcessor(BaseDataProcessor):
    """Parse a QUAST ``report.tsv`` into a two-column DataFrame.

    The QUAST file is a header followed by one ``Metric\tValue`` row per
    assembly statistic. We do not try to convert values to numeric types
    because some rows ("Assembly", "Reference length") are strings.
    """

    METRIC_COLUMN = "Metric"
    VALUE_COLUMN = "Value"

    # Subset of QUAST metrics that are useful in a clinical-virus report.
    # Order is preserved when rendering the summary table.
    HIGHLIGHTED_METRICS: tuple[str, ...] = (
        "# contigs",
        "Largest contig",
        "Total length",
        "GC (%)",
        "N50",
        "L50",
        "# N's per 100 kbp",
    )

    def _process_file(self, file_path: str | Path) -> pd.DataFrame:
        path = Path(file_path)
        try:
            df = pd.read_csv(path, sep="\t", header=0)
        except Exception as e:
            raise DataProcessingError(f"Failed to parse QUAST report {path}: {e}") from e

        if df.shape[1] < 2:
            raise DataProcessingError(f"QUAST report {path} does not have at least two columns")

        # Use the first two columns regardless of their original labels;
        # the QUAST header second column is the sample/assembly name.
        df = df.iloc[:, :2]
        df.columns = [self.METRIC_COLUMN, self.VALUE_COLUMN]
        return df

    def highlighted(self, data: pd.DataFrame) -> pd.DataFrame:
        """Return only the metrics in ``HIGHLIGHTED_METRICS``, preserving
        their declared order. Metrics absent from the report are
        skipped silently.
        """
        if data.empty:
            return data
        keep = [m for m in self.HIGHLIGHTED_METRICS if m in data[self.METRIC_COLUMN].values]
        ordered = pd.DataFrame({self.METRIC_COLUMN: keep})
        return ordered.merge(data, on=self.METRIC_COLUMN, how="left")

    def create_summary_table(
        self, data: pd.DataFrame, *, name: str | None = None, **_: Any
    ) -> pn.widgets.Tabulator:
        """Render the highlighted-metric subset as a Tabulator widget.

        ``name`` controls the sub-tab label when the widget is
        appended to a `pn.Tabs`. Callers pass the assembler name
        (e.g. ``"MEGAHIT"``) so the Assembly statistics section
        reads ``MEGAHIT`` / ``SPAdes`` / ``rnaviralSPAdes`` rather
        than three identical ``Assembly (QUAST)`` labels.
        """
        view = self.highlighted(data)
        return pn.widgets.Tabulator(
            view,
            layout="fit_columns",
            pagination=None,
            show_index=False,
            disabled=True,
            name=name or "Assembly (QUAST)",
        )
