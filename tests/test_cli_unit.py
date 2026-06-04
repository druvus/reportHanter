"""Unit tests for panel_report_cli — argument parsing, validation logic, and
the setup_logging helper.

Exercises paths that the end-to-end subprocess test (test_cli.py) does not
reach, in particular error branches and the --validate-only flag.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from reporthanter.core.exceptions import ConfigurationError
from reporthanter.panel_report_cli import (
    parse_args,
    setup_logging,
    validate_inputs,
)

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# parse_args
# ---------------------------------------------------------------------------


def _run_parse(args_list: list[str]):
    """Call parse_args with a synthetic argv and return the Namespace."""
    with patch.object(sys, "argv", ["reporthanter"] + args_list):
        return parse_args()


def test_parse_args_required_fields_only(tmp_path):
    output = str(tmp_path / "out.html")
    blast = str(FIXTURES / "blastn.csv")
    args = _run_parse(
        [
            "--blastn_file",
            blast,
            "--kraken_file",
            "kraken.tsv",
            "--kaiju_table",
            "kaiju.tsv",
            "--fastp_json",
            "fastp.json",
            "--flagstat_file",
            "flagstat.txt",
            "--mosdepth_regions",
            "regions.bed.gz",
            "--output",
            output,
        ]
    )
    assert args.output == output
    assert args.blastn_file == [blast]
    assert args.validate_only is False


def test_parse_args_validate_only_flag(tmp_path):
    output = str(tmp_path / "out.html")
    args = _run_parse(
        [
            "--blastn_file",
            "b.csv",
            "--kraken_file",
            "k.tsv",
            "--kaiju_table",
            "k2.tsv",
            "--fastp_json",
            "f.json",
            "--flagstat_file",
            "fs.txt",
            "--mosdepth_regions",
            "r.bed.gz",
            "--output",
            output,
            "--validate_only",
        ]
    )
    assert args.validate_only is True


def test_parse_args_multi_blast(tmp_path):
    output = str(tmp_path / "out.html")
    args = _run_parse(
        [
            "--blastn_file",
            "a.csv",
            "--blastn_file",
            "b.csv",
            "--kraken_file",
            "k.tsv",
            "--kaiju_table",
            "k2.tsv",
            "--fastp_json",
            "f.json",
            "--flagstat_file",
            "fs.txt",
            "--mosdepth_regions",
            "r.bed.gz",
            "--output",
            output,
        ]
    )
    assert args.blastn_file == ["a.csv", "b.csv"]


# ---------------------------------------------------------------------------
# validate_inputs (via CLI namespace)
# ---------------------------------------------------------------------------


def _make_valid_namespace(tmp_path: Path, *, output_dir_exists: bool = True):
    """Build a minimal argparse-like namespace pointing at real fixture files."""
    import argparse

    output_dir = tmp_path / "reports"
    if output_dir_exists:
        output_dir.mkdir()

    ns = argparse.Namespace(
        blastn_file=[str(FIXTURES / "blastn.csv")],
        kraken_file=str(FIXTURES / "kraken.tsv"),
        kaiju_table=str(FIXTURES / "kaiju.tsv"),
        fastp_json=str(FIXTURES / "fastp.json"),
        flagstat_file=str(FIXTURES / "flagstat.txt"),
        mosdepth_regions=str(FIXTURES / "mosdepth_regions.bed.gz"),
        secondary_flagstat_file=None,
        virus_names=None,
        quast_report=None,
        genomad_summary=None,
        output=str(output_dir / "report.html"),
    )
    return ns


def test_validate_inputs_passes_on_valid_namespace(tmp_path):
    ns = _make_valid_namespace(tmp_path)
    validate_inputs(ns)  # should not raise


def test_validate_inputs_missing_output_dir(tmp_path):
    ns = _make_valid_namespace(tmp_path, output_dir_exists=False)
    with pytest.raises(ConfigurationError):
        validate_inputs(ns)


def test_validate_inputs_missing_blast(tmp_path):
    import argparse

    output_dir = tmp_path / "out"
    output_dir.mkdir()
    ns = argparse.Namespace(
        blastn_file=[str(tmp_path / "no_blast.csv")],
        kraken_file=str(FIXTURES / "kraken.tsv"),
        kaiju_table=str(FIXTURES / "kaiju.tsv"),
        fastp_json=str(FIXTURES / "fastp.json"),
        flagstat_file=str(FIXTURES / "flagstat.txt"),
        mosdepth_regions=str(FIXTURES / "mosdepth_regions.bed.gz"),
        secondary_flagstat_file=None,
        virus_names=None,
        quast_report=None,
        genomad_summary=None,
        output=str(output_dir / "report.html"),
    )
    with pytest.raises(ConfigurationError):
        validate_inputs(ns)


# ---------------------------------------------------------------------------
# setup_logging
# ---------------------------------------------------------------------------


def test_setup_logging_does_not_raise():
    """setup_logging should run without raising regardless of the root handler state."""
    # pytest installs its own root handler, so basicConfig may be a no-op;
    # we only verify that the call succeeds for all supported levels.
    for level in ("DEBUG", "INFO", "WARNING", "ERROR"):
        setup_logging(level)


def test_setup_logging_with_config_does_not_raise():
    from reporthanter.core.config import DefaultConfig

    config = DefaultConfig()
    setup_logging("WARNING", config)
