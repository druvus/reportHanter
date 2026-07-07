"""Tests for FastpProcessor."""

import json
from pathlib import Path

import pytest

from reporthanter.core.exceptions import DataProcessingError, ReportHanterError
from reporthanter.processors.fastp_processor import FastpProcessor

FIXTURES = Path(__file__).parent / "fixtures"


def test_process_extracts_summary_table():
    proc = FastpProcessor()
    df = proc.process(str(FIXTURES / "fastp.json"))

    metrics = dict(zip(df["Metric"], df["Value"], strict=False))
    assert metrics["sequencing"].startswith("paired end")
    assert "0.23.4" in metrics["fastp version"]
    # Q20 after filtering is 0.98 -> "98.0%"
    assert "98.0%" in metrics["Q20 bases"]
    # Mean length after filtering rendered as "148bp, 148bp"
    assert "148" in metrics["mean length after filtering"]


def test_validate_rejects_invalid_json(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")

    proc = FastpProcessor()
    with pytest.raises(DataProcessingError):
        proc.validate_input(bad)


def test_validate_rejects_missing_summary(tmp_path):
    bad = tmp_path / "no_summary.json"
    bad.write_text(json.dumps({"something": "else"}))

    proc = FastpProcessor()
    with pytest.raises(DataProcessingError):
        proc.validate_input(bad)


# ---------------------------------------------------------------------------
# Structure validation in _process_file
# ---------------------------------------------------------------------------


def test_process_raises_on_missing_summary_section(tmp_path):
    """_process_file raises ReportHanterError when 'summary' is absent."""
    bad = tmp_path / "no_summary.json"
    bad.write_text(json.dumps({"filtering_result": {}}))

    proc = FastpProcessor()
    with pytest.raises(ReportHanterError, match="'summary'"):
        proc._process_file(bad)


def test_process_raises_on_missing_before_filtering(tmp_path):
    """_process_file raises when 'before_filtering' is absent from summary."""
    bad = tmp_path / "partial.json"
    bad.write_text(
        json.dumps(
            {
                "summary": {"after_filtering": {}},
                "filtering_result": {},
            }
        )
    )
    proc = FastpProcessor()
    with pytest.raises(ReportHanterError, match="before_filtering"):
        proc._process_file(bad)


def test_process_raises_on_missing_after_filtering(tmp_path):
    bad = tmp_path / "partial.json"
    bad.write_text(
        json.dumps(
            {
                "summary": {"before_filtering": {}},
                "filtering_result": {},
            }
        )
    )
    proc = FastpProcessor()
    with pytest.raises(ReportHanterError, match="after_filtering"):
        proc._process_file(bad)


def test_process_raises_on_missing_filtering_result(tmp_path):
    bad = tmp_path / "partial.json"
    bad.write_text(
        json.dumps(
            {
                "summary": {
                    "before_filtering": {},
                    "after_filtering": {},
                },
            }
        )
    )
    proc = FastpProcessor()
    with pytest.raises(ReportHanterError, match="filtering_result"):
        proc._process_file(bad)


def test_process_handles_zero_reads(tmp_path):
    """A sample with no surviving reads carries "total_reads": 0 in
    before_filtering; the filter-percentage divisions must not crash."""
    empty = tmp_path / "empty_sample.json"
    empty.write_text(
        json.dumps(
            {
                "summary": {
                    "fastp_version": "0.23.4",
                    "before_filtering": {"total_reads": 0},
                    "after_filtering": {"total_reads": 0},
                },
                "filtering_result": {
                    "passed_filter_reads": 0,
                    "low_quality_reads": 0,
                    "too_many_N_reads": 0,
                    "too_short_reads": 0,
                },
            }
        )
    )
    proc = FastpProcessor()
    df = proc.process(str(empty))
    metrics = dict(zip(df["Metric"], df["Value"], strict=False))
    assert "0.0%" in metrics["reads passed filters"]
    assert "0.0 K" in metrics["total reads"]
