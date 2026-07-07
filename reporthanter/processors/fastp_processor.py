"""
FastP data processor with improved error handling and configuration.
"""

import json
from pathlib import Path
from typing import Any

import pandas as pd
import panel as pn

from ..core.base import BaseDataProcessor
from ..core.exceptions import DataProcessingError, ReportHanterError


class FastpProcessor(BaseDataProcessor):
    """Processes FastP JSON files into summary statistics."""

    def validate_input(self, file_path: str | Path) -> bool:
        """Validate FastP JSON file format."""
        super().validate_input(file_path)

        try:
            with open(file_path) as f:
                data = json.load(f)

            # Check for required sections
            if "summary" not in data:
                raise DataProcessingError("Missing 'summary' section in FastP JSON")

        except json.JSONDecodeError as e:
            raise DataProcessingError(f"Invalid JSON format: {e}") from e
        except Exception as e:
            raise DataProcessingError(f"Error validating FastP JSON: {e}") from e

        return True

    def _process_file(self, file_path: str | Path) -> pd.DataFrame:
        """Process FastP JSON file into summary statistics.

        Validates that the expected top-level keys are present before
        attempting extraction, raising
        :exc:`~reporthanter.core.exceptions.ReportHanterError` rather
        than silently yielding zero-percent values when the JSON
        structure does not match the expected fastp schema.
        """
        with open(file_path) as f:
            data = json.load(f)

        # Structural validation: require the keys the extractor relies on.
        if "summary" not in data:
            raise ReportHanterError(
                f"FastP JSON {file_path} is missing the required 'summary' section. "
                "Check that the file is a valid fastp JSON report."
            )
        summary = data["summary"]
        for section in ("before_filtering", "after_filtering"):
            if section not in summary:
                raise ReportHanterError(
                    f"FastP JSON {file_path}: 'summary' is missing the "
                    f"required '{section}' sub-section."
                )
        if "filtering_result" not in data:
            raise ReportHanterError(
                f"FastP JSON {file_path} is missing the required 'filtering_result' section."
            )

        stats = self._extract_statistics(data)

        # Convert to DataFrame for consistency with other processors.
        return pd.DataFrame(list(stats.items()), columns=["Metric", "Value"])

    def _extract_statistics(self, data: dict[str, Any]) -> dict[str, str]:
        """Extract summary statistics from FastP JSON data."""
        summary = data.get("summary", {})
        before = summary.get("before_filtering", {})
        after = summary.get("after_filtering", {})
        duplication = data.get("duplication", {})
        insert_size = data.get("insert_size", {})
        filtering = data.get("filtering_result", {})

        # Basic info
        version = summary.get("fastp_version", "N/A")
        sequencing = summary.get("sequencing", "N/A")

        # Read lengths
        mean_length_before = f"{before.get('read1_mean_length', 'N/A')}bp, {before.get('read2_mean_length', 'N/A')}bp"
        mean_length_after = (
            f"{after.get('read1_mean_length', 'N/A')}bp, {after.get('read2_mean_length', 'N/A')}bp"
        )

        # Quality metrics
        dup_rate = duplication.get("rate", 0) * 100
        insert_peak = insert_size.get("peak", "N/A")

        # After-filtering stats
        total_reads = after.get("total_reads", 0)
        total_bases = after.get("total_bases", 0)
        q20_bases = after.get("q20_bases", 0)
        q30_bases = after.get("q30_bases", 0)
        q20_rate = after.get("q20_rate", 0) * 100
        q30_rate = after.get("q30_rate", 0) * 100
        gc_content = after.get("gc_content", 0) * 100

        # Filtering results
        # Avoid division by zero. `.get(..., 1)` only defends against a
        # missing key; a sample with no surviving reads carries an
        # explicit "total_reads": 0, so fall back to 1 whenever the value
        # is absent or zero. The numerators are then all zero, giving a
        # sensible 0.0% for every filter category.
        total_reads_before = before.get("total_reads", 0) or 1
        passed = filtering.get("passed_filter_reads", 0)
        low_quality = filtering.get("low_quality_reads", 0)
        too_many_N = filtering.get("too_many_N_reads", 0)
        too_short = filtering.get("too_short_reads", 0)

        # Calculate percentages
        reads_passed_pct = (passed / total_reads_before) * 100
        low_quality_pct = (low_quality / total_reads_before) * 100
        too_many_N_pct = (too_many_N / total_reads_before) * 100
        too_short_pct = (too_short / total_reads_before) * 100

        return {
            "fastp version": f"{version} (https://github.com/OpenGene/fastp)",
            "sequencing": sequencing,
            "mean length before filtering": mean_length_before,
            "mean length after filtering": mean_length_after,
            "duplication rate": f"{dup_rate:.2f}%",
            "Insert size peak": str(insert_peak),
            "total reads": f"{total_reads / 1000:.1f} K",
            "total bases": f"{total_bases / 1e6:.1f} M",
            "Q20 bases": f"{q20_bases / 1e6:.1f} M ({q20_rate:.1f}%)",
            "Q30 bases": f"{q30_bases / 1e6:.1f} M ({q30_rate:.1f}%)",
            "GC content": f"{gc_content:.1f}%",
            "reads passed filters": f"{passed / 1000:.1f} K ({reads_passed_pct:.1f}%)",
            "reads with low quality": f"{low_quality / 1000:.1f} K ({low_quality_pct:.1f}%)",
            "reads with too many N": f"{too_many_N} ({too_many_N_pct:.2f}%)",
            "reads too short": f"{too_short} ({too_short_pct:.2f}%)",
        }

    def create_summary_table(self, data: pd.DataFrame, **kwargs: Any) -> pn.widgets.Tabulator:
        """Create a Panel Tabulator widget from FastP statistics."""
        table_name = kwargs.get("name", "FASTP Report Summary")

        table = pn.widgets.Tabulator(
            data,
            layout="fit_columns",
            show_index=False,
            name=table_name,
            pagination="local",
            page_size=20,
        )

        return table
