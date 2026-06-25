"""Tests for FlagstatProcessor."""

from pathlib import Path

import pytest

from reporthanter.core.exceptions import DataProcessingError
from reporthanter.processors.flagstat_processor import FlagstatProcessor

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_well_formed_flagstat():
    proc = FlagstatProcessor()
    df = proc.process(str(FIXTURES / "flagstat.txt"))

    lookup = dict(zip(df["metric"], df["value"], strict=False))
    assert lookup["total_reads"] == 2000
    assert lookup["percent_mapped"] == pytest.approx(72.5)
    assert lookup["reads_mapped"] == 1450
    assert lookup["reads_unmapped"] == 550


def test_over_100_percent_mapped_is_clamped(tmp_path):
    # Some samtools outputs count supplementary / secondary alignments so
    # "with itself and mate mapped" exceeds "paired in sequencing". The
    # mapped percentage must clamp to 100 and unmapped must not go
    # negative.
    flagstat = tmp_path / "flagstat_over100.txt"
    flagstat.write_text("1000 + 0 paired in sequencing\n1200 + 0 with itself and mate mapped\n")
    proc = FlagstatProcessor()
    df = proc.process(str(flagstat))

    lookup = dict(zip(df["metric"], df["value"], strict=False))
    assert lookup["percent_mapped"] == 100.0
    assert lookup["reads_mapped"] == 1000
    assert lookup["reads_unmapped"] == 0


def test_zero_total_reads_does_not_divide_by_zero():
    proc = FlagstatProcessor()
    df = proc.process(str(FIXTURES / "flagstat_zero.txt"))

    lookup = dict(zip(df["metric"], df["value"], strict=False))
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


def test_malformed_flagstat_missing_paired_line_raises_clear_error(tmp_path):
    """_parse_flagstat raises DataProcessingError naming the file when
    the 'paired in sequencing' line is absent.

    This guards against future samtools output-format changes that
    drop or rename that line, ensuring a clear diagnostic rather than
    a raw IndexError.
    """
    proc = FlagstatProcessor()
    malformed = tmp_path / "flagstat_malformed.txt"
    # Contains 'with itself and mate mapped' but not 'paired in sequencing'.
    malformed.write_text(
        "1500 + 0 with itself and mate mapped\n"
        "50 + 0 singletons (2.50% : N/A)\n"
        "paired in sequencing\n"  # no leading integer pattern
    )

    with pytest.raises(DataProcessingError, match="paired in sequencing"):
        proc.process(str(malformed))


def test_malformed_flagstat_missing_mapped_line_raises_clear_error(tmp_path):
    """_parse_flagstat raises DataProcessingError naming the file when
    the 'with itself and mate mapped' line is absent.
    """
    proc = FlagstatProcessor()
    malformed = tmp_path / "flagstat_no_mapped.txt"
    # Contains 'paired in sequencing' but not 'with itself and mate mapped'.
    malformed.write_text("2000 + 0 paired in sequencing\n1000 + 0 read1\n1000 + 0 read2\n")

    with pytest.raises(DataProcessingError, match="with itself and mate mapped"):
        proc.process(str(malformed))
