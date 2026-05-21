"""geNomad virus_summary processor.

Parses a geNomad ``<sample>_virus_summary.tsv`` (the per-sample
output of ``genomad end-to-end``) into a tidy DataFrame and exposes
a small summary table for the report.

The file is a tab-separated header followed by one row per contig
that geNomad called viral, with the schema documented at
https://portal.nersc.gov/genomad/. The columns the report cares
about are ``seq_name``, ``length``, ``virus_score``, ``fdr``,
``n_hallmarks`` and ``taxonomy``.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import panel as pn

from ..core.base import BaseDataProcessor
from ..core.exceptions import DataProcessingError


class GenomadProcessor(BaseDataProcessor):
    """Parse a geNomad virus_summary TSV into a tidy DataFrame."""

    HIGHLIGHTED_COLUMNS: tuple[str, ...] = (
        "seq_name",
        "length",
        "virus_score",
        "fdr",
        "n_hallmarks",
        "taxonomy",
    )

    def _process_file(self, file_path: str | Path) -> pd.DataFrame:
        path = Path(file_path)
        try:
            df = pd.read_csv(path, sep="\t")
        except Exception as e:
            raise DataProcessingError(f"Failed to parse geNomad virus_summary {path}: {e}") from e
        if df.empty:
            return df
        # geNomad headers are stable across versions; keep only the
        # columns we know how to display. Missing columns degrade
        # gracefully (we silently drop them from the highlighted set).
        keep = [c for c in self.HIGHLIGHTED_COLUMNS if c in df.columns]
        if not keep:
            return pd.DataFrame()
        return df[keep].copy()

    def create_summary_table(self, data: pd.DataFrame) -> pn.widgets.Tabulator:
        """Render geNomad's viral-contig calls as a Tabulator widget.

        Contigs are sorted by ``virus_score`` descending so the most
        confident calls land at the top.
        """
        if data.empty:
            return pn.widgets.Tabulator(
                pd.DataFrame({"info": ["geNomad called no viral contigs."]}),
                layout="fit_columns",
                pagination=None,
                show_index=False,
                disabled=True,
                name="geNomad",
            )
        view = data.copy()
        if "virus_score" in view.columns:
            view = view.sort_values("virus_score", ascending=False)
        return pn.widgets.Tabulator(
            view,
            layout="fit_columns",
            pagination="local",
            page_size=15,
            show_index=False,
            disabled=True,
            name="geNomad",
        )
