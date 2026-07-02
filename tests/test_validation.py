"""Tests for the shared input-file validation service."""

from __future__ import annotations

from pathlib import Path

import pytest

from reporthanter.core.exceptions import ConfigurationError
from reporthanter.core.validation import validate_report_inputs

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Happy path: all required files present
# ---------------------------------------------------------------------------


def test_valid_inputs_pass(tmp_path):
    """validate_report_inputs raises nothing when all required files are present."""
    blast = tmp_path / "blast.csv"
    blast.write_text("match_name,accession\nHerpes,NC_001\n")

    validate_report_inputs(
        kraken_file=str(FIXTURES / "kraken.tsv"),
        kaiju_table=str(FIXTURES / "kaiju.tsv"),
        fastp_json=str(FIXTURES / "fastp.json"),
        flagstat_file=str(FIXTURES / "flagstat.txt"),
        mosdepth_regions=str(FIXTURES / "mosdepth_regions.bed.gz"),
        blastn_files=[str(blast)],
    )


# ---------------------------------------------------------------------------
# Missing required files
# ---------------------------------------------------------------------------


def test_missing_kraken_raises(tmp_path):
    blast = tmp_path / "blast.csv"
    blast.write_text("x\n")
    mosdepth = tmp_path / "cov.bed.gz"
    mosdepth.write_bytes(b"\x1f\x8b\x00")  # minimal non-empty gz

    with pytest.raises(ConfigurationError, match="1 error"):
        validate_report_inputs(
            kraken_file=str(tmp_path / "missing_kraken.tsv"),
            kaiju_table=str(FIXTURES / "kaiju.tsv"),
            fastp_json=str(FIXTURES / "fastp.json"),
            flagstat_file=str(FIXTURES / "flagstat.txt"),
            mosdepth_regions=str(FIXTURES / "mosdepth_regions.bed.gz"),
            blastn_files=[str(blast)],
        )


def test_multiple_missing_files_collects_all_errors(tmp_path):
    """All violations are collected before raising, not fail-fast."""
    with pytest.raises(ConfigurationError) as exc_info:
        validate_report_inputs(
            kraken_file=str(tmp_path / "no_kraken.tsv"),
            kaiju_table=str(tmp_path / "no_kaiju.tsv"),
            fastp_json=str(FIXTURES / "fastp.json"),
            flagstat_file=str(FIXTURES / "flagstat.txt"),
            mosdepth_regions=str(FIXTURES / "mosdepth_regions.bed.gz"),
            blastn_files=[str(FIXTURES / "blastn.csv")],
        )
    # Both missing files must be mentioned
    assert "2 error" in str(exc_info.value)


def test_no_blast_files_raises():
    """An empty blastn_files list triggers a validation error."""
    with pytest.raises(ConfigurationError):
        validate_report_inputs(
            kraken_file=str(FIXTURES / "kraken.tsv"),
            kaiju_table=str(FIXTURES / "kaiju.tsv"),
            fastp_json=str(FIXTURES / "fastp.json"),
            flagstat_file=str(FIXTURES / "flagstat.txt"),
            mosdepth_regions=str(FIXTURES / "mosdepth_regions.bed.gz"),
            blastn_files=[],
        )


# ---------------------------------------------------------------------------
# Empty files
# ---------------------------------------------------------------------------


def test_empty_required_file_raises(tmp_path):
    """A zero-byte still-required file (FastP) is rejected."""
    empty_fastp = tmp_path / "empty_fastp.json"
    empty_fastp.touch()

    with pytest.raises(ConfigurationError):
        validate_report_inputs(
            kraken_file=str(FIXTURES / "kraken.tsv"),
            kaiju_table=str(FIXTURES / "kaiju.tsv"),
            fastp_json=str(empty_fastp),
            flagstat_file=str(FIXTURES / "flagstat.txt"),
            mosdepth_regions=str(FIXTURES / "mosdepth_regions.bed.gz"),
            blastn_files=[str(FIXTURES / "blastn.csv")],
        )


def test_empty_kraken_and_kaiju_are_tolerated(tmp_path):
    """Zero-byte Kraken/Kaiju reports pass validation (zero reads reaching
    classification): the report renders with empty Classification charts."""
    empty_kraken = tmp_path / "empty_kraken.tsv"
    empty_kraken.touch()
    empty_kaiju = tmp_path / "empty_kaiju.tsv"
    empty_kaiju.touch()

    # Must not raise.
    validate_report_inputs(
        kraken_file=str(empty_kraken),
        kaiju_table=str(empty_kaiju),
        fastp_json=str(FIXTURES / "fastp.json"),
        flagstat_file=str(FIXTURES / "flagstat.txt"),
        mosdepth_regions=str(FIXTURES / "mosdepth_regions.bed.gz"),
        blastn_files=[str(FIXTURES / "blastn.csv")],
    )


def test_missing_kraken_still_raises(tmp_path):
    """Tolerating *empty* does not tolerate *missing*: a non-existent
    Kraken file is still a validation error."""
    with pytest.raises(ConfigurationError):
        validate_report_inputs(
            kraken_file=str(tmp_path / "absent_kraken.tsv"),
            kaiju_table=str(FIXTURES / "kaiju.tsv"),
            fastp_json=str(FIXTURES / "fastp.json"),
            flagstat_file=str(FIXTURES / "flagstat.txt"),
            mosdepth_regions=str(FIXTURES / "mosdepth_regions.bed.gz"),
            blastn_files=[str(FIXTURES / "blastn.csv")],
        )


def test_empty_blast_csv_is_tolerated(tmp_path):
    """Empty BLAST CSVs are accepted (no contigs = valid result)."""
    empty_blast = tmp_path / "empty_blast.csv"
    empty_blast.touch()

    # Must not raise
    validate_report_inputs(
        kraken_file=str(FIXTURES / "kraken.tsv"),
        kaiju_table=str(FIXTURES / "kaiju.tsv"),
        fastp_json=str(FIXTURES / "fastp.json"),
        flagstat_file=str(FIXTURES / "flagstat.txt"),
        mosdepth_regions=str(FIXTURES / "mosdepth_regions.bed.gz"),
        blastn_files=[str(empty_blast)],
    )


# ---------------------------------------------------------------------------
# Optional inputs
# ---------------------------------------------------------------------------


def test_optional_missing_secondary_flagstat_raises(tmp_path):
    """Optional secondary flagstat that is supplied but missing triggers an error."""
    with pytest.raises(ConfigurationError):
        validate_report_inputs(
            kraken_file=str(FIXTURES / "kraken.tsv"),
            kaiju_table=str(FIXTURES / "kaiju.tsv"),
            fastp_json=str(FIXTURES / "fastp.json"),
            flagstat_file=str(FIXTURES / "flagstat.txt"),
            mosdepth_regions=str(FIXTURES / "mosdepth_regions.bed.gz"),
            blastn_files=[str(FIXTURES / "blastn.csv")],
            secondary_flagstat_file=str(tmp_path / "no_secondary.txt"),
        )


def test_optional_not_supplied_is_fine():
    """Leaving all optionals as None raises nothing."""
    validate_report_inputs(
        kraken_file=str(FIXTURES / "kraken.tsv"),
        kaiju_table=str(FIXTURES / "kaiju.tsv"),
        fastp_json=str(FIXTURES / "fastp.json"),
        flagstat_file=str(FIXTURES / "flagstat.txt"),
        mosdepth_regions=str(FIXTURES / "mosdepth_regions.bed.gz"),
        blastn_files=[str(FIXTURES / "blastn.csv")],
        secondary_flagstat_file=None,
        virus_names=None,
        quast_reports=None,
        genomad_summaries=None,
    )


def test_quast_list_validates_each_entry(tmp_path):
    """Every path in the quast_reports list is checked."""
    with pytest.raises(ConfigurationError):
        validate_report_inputs(
            kraken_file=str(FIXTURES / "kraken.tsv"),
            kaiju_table=str(FIXTURES / "kaiju.tsv"),
            fastp_json=str(FIXTURES / "fastp.json"),
            flagstat_file=str(FIXTURES / "flagstat.txt"),
            mosdepth_regions=str(FIXTURES / "mosdepth_regions.bed.gz"),
            blastn_files=[str(FIXTURES / "blastn.csv")],
            quast_reports=[str(tmp_path / "no_quast.tsv")],
        )
