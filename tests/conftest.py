"""Shared pytest fixtures for the reporthanter test suite.

Centralises the per-module ``FIXTURES`` constant, the processor
defaults used by ``test_processors.py`` and the kwargs the
Dashboard smoke uses so each test file can focus on the assertion
it actually cares about.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from reporthanter import FastpProcessor, KrakenProcessor

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Path to the on-disk test-fixture directory."""
    return FIXTURES_DIR


@pytest.fixture
def kraken_processor() -> KrakenProcessor:
    """Fresh ``KrakenProcessor`` with default config.

    Function-scoped so tests that mutate processor state stay
    isolated; the construction is cheap.
    """
    return KrakenProcessor()


@pytest.fixture
def fastp_processor() -> FastpProcessor:
    """Fresh ``FastpProcessor`` with default config."""
    return FastpProcessor()


@pytest.fixture
def dashboard_kwargs(fixtures_dir: Path) -> dict:
    """Canonical kwargs for the Dashboard smoke. Tests can override
    individual keys via ``{**dashboard_kwargs, "blastn_files": []}``
    to probe specific branches.
    """
    return {
        "sample_name": "smoke",
        "fastp_json": str(fixtures_dir / "fastp.json"),
        "flagstat_file": str(fixtures_dir / "flagstat.txt"),
        "kraken_file": str(fixtures_dir / "kraken.tsv"),
        "kaiju_table": str(fixtures_dir / "kaiju.tsv"),
        "blastn_files": [str(fixtures_dir / "blastn.csv")],
        "quast_reports": [],
        "mosdepth_regions": str(fixtures_dir / "mosdepth_regions.bed.gz"),
        "virus_names": None,
    }
