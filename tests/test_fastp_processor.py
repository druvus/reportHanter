"""Tests for FastpProcessor."""
import json
from pathlib import Path

import pytest

from reporthanter.core.exceptions import DataProcessingError
from reporthanter.processors.fastp_processor import FastpProcessor


FIXTURES = Path(__file__).parent / "fixtures"


def test_process_extracts_summary_table():
    proc = FastpProcessor()
    df = proc.process(str(FIXTURES / "fastp.json"))

    metrics = dict(zip(df["Metric"], df["Value"]))
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
