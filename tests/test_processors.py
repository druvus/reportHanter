"""
Tests for data processors.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from reporthanter.core.exceptions import DataProcessingError, FileValidationError

# ---------------------------------------------------------------------------
# KrakenProcessor
# ---------------------------------------------------------------------------


class TestKrakenProcessor:
    """Test the KrakenProcessor class."""

    def test_validate_input_missing_file(self, kraken_processor):
        with pytest.raises(FileValidationError, match="File does not exist"):
            kraken_processor.validate_input("/nonexistent/file.tsv")

    def test_validate_input_empty_file(self, kraken_processor, tmp_path):
        empty_file = tmp_path / "empty.tsv"
        empty_file.touch()
        with pytest.raises(FileValidationError, match="File is empty"):
            kraken_processor.validate_input(empty_file)

    def test_validate_input_valid_kraken_file(self, kraken_processor, tmp_path):
        kraken_file = tmp_path / "ok.tsv"
        kraken_file.write_text("10.5\t100\t50\tS\t123\tVirus species\n")
        assert kraken_processor.validate_input(kraken_file) is True

    def test_process_kraken_file(self, kraken_processor, tmp_path):
        kraken_file = tmp_path / "k.tsv"
        kraken_file.write_text(
            "10.5\t100\t50\tD\tViruses\tViruses\n"
            "5.2\t50\t25\tS\t123\tViral species\n"
            "84.3\t800\t400\tU\t0\tunclassified\n"
        )
        df = kraken_processor.process(kraken_file)

        assert len(df) == 3
        assert "percent" in df.columns
        assert "domain" in df.columns
        # 10.5% -> 0.105 after the parser's /100 normalisation.
        assert df.loc[0, "percent"] == 0.105
        # The 'D' row's domain forward-fills onto the following species row.
        assert df.loc[1, "domain"] == "Viruses"
        assert df.loc[2, "domain"] == "unclassified"

    def test_filter_data_species_level(self, kraken_processor):
        data = pd.DataFrame(
            {
                "percent": [0.8, 0.1, 0.05, 0.02, 0.01],
                "count_clades": [800, 100, 50, 20, 10],
                "tax_lvl": ["U", "S", "S", "S", "S"],
                "name": ["unclassified", "Virus A", "Virus B", "Virus C", "Virus D"],
                "domain": [
                    "unclassified",
                    "Viruses",
                    "Viruses",
                    "Viruses",
                    "Viruses",
                ],
            }
        )

        filtered_df, unclassified_pct = kraken_processor.filter_data(
            data, level="species", cutoff=0.03, max_entries=2, virus_only=True
        )

        assert unclassified_pct == 0.8
        assert len(filtered_df) == 2
        assert all(filtered_df["percent"] > 0.03)
        assert all(filtered_df["domain"] == "Viruses")
        assert filtered_df.iloc[0]["name"] == "Virus A"

    def test_filter_data_empty_dataframe_returns_empty_and_zero(self, kraken_processor):
        """filter_data on an empty DataFrame must not raise IndexError.

        An empty Kraken report is not expected in practice, but the
        guard must degrade gracefully rather than propagating a raw
        IndexError from .iloc[0].
        """
        empty = pd.DataFrame(
            columns=["percent", "count_clades", "count", "tax_lvl", "name", "domain"]
        )
        filtered_df, unclassified_pct = kraken_processor.filter_data(empty, level="species")

        assert filtered_df.empty
        assert unclassified_pct == 0.0

    def test_filter_data_no_unclassified_row(self, kraken_processor):
        """filter_data returns unclassified_pct=0.0 when no 'unclassified' domain is present."""
        data = pd.DataFrame(
            {
                "percent": [0.10, 0.05],
                "count_clades": [100, 50],
                "count": [80, 40],
                "tax_lvl": ["S", "S"],
                "name": ["Virus A", "Virus B"],
                "domain": ["Viruses", "Viruses"],
            }
        )
        _, unclassified_pct = kraken_processor.filter_data(data, level="species")
        assert unclassified_pct == 0.0


# ---------------------------------------------------------------------------
# FastpProcessor
# ---------------------------------------------------------------------------


def _write_json(tmp_path: Path, name: str, payload: dict | str) -> Path:
    """Write ``payload`` (dict or raw string) into ``tmp_path/name`` and
    return the path. Keeps the fastp tests' setup to one line."""
    p = tmp_path / name
    p.write_text(json.dumps(payload) if isinstance(payload, dict) else payload)
    return p


_FASTP_FULL_PAYLOAD: dict = {
    "summary": {
        "fastp_version": "0.20.0",
        "sequencing": "paired end",
        "before_filtering": {
            "total_reads": 1000,
            "read1_mean_length": 150,
            "read2_mean_length": 150,
        },
        "after_filtering": {
            "total_reads": 900,
            "total_bases": 135000,
            "q20_bases": 120000,
            "q30_bases": 100000,
            "q20_rate": 0.89,
            "q30_rate": 0.74,
            "gc_content": 0.45,
            "read1_mean_length": 148,
            "read2_mean_length": 148,
        },
    },
    "duplication": {"rate": 0.05},
    "insert_size": {"peak": 300},
    "filtering_result": {
        "passed_filter_reads": 900,
        "low_quality_reads": 80,
        "too_many_N_reads": 10,
        "too_short_reads": 10,
    },
}


class TestFastpProcessor:
    """Test the FastpProcessor class."""

    def test_validate_input_valid_json(self, fastp_processor, tmp_path):
        json_file = _write_json(
            tmp_path,
            "fastp.json",
            {
                "summary": {
                    "before_filtering": {"total_reads": 1000},
                    "after_filtering": {"total_reads": 900},
                }
            },
        )
        assert fastp_processor.validate_input(json_file) is True

    def test_validate_input_invalid_json(self, fastp_processor, tmp_path):
        json_file = _write_json(tmp_path, "bad.json", "invalid json")
        with pytest.raises(DataProcessingError, match="Invalid JSON format"):
            fastp_processor.validate_input(json_file)

    def test_process_fastp_file(self, fastp_processor, tmp_path):
        json_file = _write_json(tmp_path, "fastp.json", _FASTP_FULL_PAYLOAD)
        df = fastp_processor.process(json_file)

        assert len(df) > 0
        assert "Metric" in df.columns
        assert "Value" in df.columns

        metrics_dict = dict(zip(df["Metric"], df["Value"], strict=False))
        assert "fastp version" in metrics_dict
        assert "0.20.0" in metrics_dict["fastp version"]
        assert "total reads" in metrics_dict
        # 900 reads after filtering renders as "0.9 K".
        assert "0.9 K" in metrics_dict["total reads"]
