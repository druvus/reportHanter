"""Tests for FlagstatProcessor."""
from pathlib import Path

import pytest

from reporthanter.core.exceptions import DataProcessingError
from reporthanter.processors.flagstat_processor import FlagstatProcessor


FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_well_formed_flagstat():
    proc = FlagstatProcessor()
    df = proc.process(str(FIXTURES / "flagstat.txt"))

    lookup = dict(zip(df["metric"], df["value"]))
    assert lookup["total_reads"] == 2000
    assert lookup["percent_mapped"] == pytest.approx(72.5)
    assert lookup["reads_mapped"] == 1450
    assert lookup["reads_unmapped"] == 550


def test_zero_total_reads_does_not_divide_by_zero():
    proc = FlagstatProcessor()
    df = proc.process(str(FIXTURES / "flagstat_zero.txt"))

    lookup = dict(zip(df["metric"], df["value"]))
    assert lookup["total_reads"] == 0
    assert lookup["percent_mapped"] == 0.0
    assert lookup["reads_mapped"] == 0
    assert lookup["reads_unmapped"] == 0


def test_validate_rejects_non_flagstat_file(tmp_path):
    proc = FlagstatProcessor()
    bogus = tmp_path / "bogus.txt"
    bogus.write_text("this is not flagstat output")

    with pytest.raises(DataProcessingError):
        proc.validate_input(bogus)
