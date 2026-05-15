"""Tests for BlastProcessor (no subprocess invocation)."""
from pathlib import Path

import pandas as pd
import pytest

from reporthanter.core.exceptions import DataProcessingError, FileValidationError
from reporthanter.processors.blast_processor import BlastProcessor


FIXTURES = Path(__file__).parent / "fixtures"


def test_process_reads_csv_unchanged():
    proc = BlastProcessor()
    df = proc.process(str(FIXTURES / "blastn.csv"))

    assert {"name", "match_name", "accession", "percent_identity"}.issubset(df.columns)
    assert len(df) == 3


def test_validate_accepts_well_formed_csv():
    proc = BlastProcessor()
    assert proc.validate_input(FIXTURES / "blastn.csv") is True


def test_validate_rejects_missing_file(tmp_path):
    proc = BlastProcessor()
    with pytest.raises((FileValidationError, DataProcessingError)):
        proc.validate_input(tmp_path / "does_not_exist.csv")


def test_empty_csv_round_trips(tmp_path):
    empty = tmp_path / "empty.csv"
    pd.DataFrame(columns=["name", "match_name"]).to_csv(empty, index=False)

    proc = BlastProcessor()
    df = proc.process(str(empty))
    assert df.empty
    assert list(df.columns) == ["name", "match_name"]
