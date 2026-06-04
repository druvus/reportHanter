"""In-process integration tests for ReportGenerator.

Running the report generator in the same process (rather than via
subprocess like test_cli.py) allows pytest-cov to measure the section
builders, generators, and helper utilities inside generator.py and
sections.py.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from reporthanter.core.config import DefaultConfig
from reporthanter.core.exceptions import ReportGenerationError
from reporthanter.report.generator import ReportGenerator

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def generator():
    return ReportGenerator(DefaultConfig())


@pytest.fixture(scope="module")
def full_report(generator):
    """Generate one complete report from the fixture files.  Cached at module
    scope so the expensive Panel/Altair render runs only once per test session.
    """
    return generator.generate_report(
        blastn_files=[str(FIXTURES / "blastn.csv")],
        kraken_file=str(FIXTURES / "kraken.tsv"),
        kaiju_table=str(FIXTURES / "kaiju.tsv"),
        fastp_json=str(FIXTURES / "fastp.json"),
        flagstat_file=str(FIXTURES / "flagstat.txt"),
        mosdepth_regions=str(FIXTURES / "mosdepth_regions.bed.gz"),
        sample_name="pytest_sample",
    )


# ---------------------------------------------------------------------------
# Basic structural smoke test
# ---------------------------------------------------------------------------


def test_generate_report_returns_panel_column(full_report):
    import panel as pn

    assert isinstance(full_report, pn.Column)


def test_generate_report_has_header_and_tabs(full_report):
    # The Column is [header, Divider, Tabs].
    assert len(full_report.objects) >= 3


def test_generate_report_tabs_have_seven_sections(full_report):
    import panel as pn

    tabs = next(o for o in full_report.objects if isinstance(o, pn.Tabs))
    assert len(tabs) == 7


# ---------------------------------------------------------------------------
# save_report
# ---------------------------------------------------------------------------


def test_save_report_writes_html(generator, full_report, tmp_path):
    output = tmp_path / "report.html"
    generator.save_report(full_report, output, title="pytest")
    assert output.exists()
    assert output.stat().st_size > 10_000


def test_save_report_raises_on_bad_path(generator, full_report):
    with pytest.raises(ReportGenerationError):
        generator.save_report(full_report, "/no/such/dir/report.html")


# ---------------------------------------------------------------------------
# Error handling: missing required blast files
# ---------------------------------------------------------------------------


def test_generate_report_raises_without_blast_files(generator):
    with pytest.raises(ReportGenerationError, match="BLAST CSV"):
        generator.generate_report(
            kraken_file=str(FIXTURES / "kraken.tsv"),
            kaiju_table=str(FIXTURES / "kaiju.tsv"),
            fastp_json=str(FIXTURES / "fastp.json"),
            flagstat_file=str(FIXTURES / "flagstat.txt"),
            mosdepth_regions=str(FIXTURES / "mosdepth_regions.bed.gz"),
        )


# ---------------------------------------------------------------------------
# _create_main_header
# ---------------------------------------------------------------------------


def test_create_main_header_contains_sample_name(generator):
    import panel as pn

    header = generator._create_main_header("MySample")
    assert isinstance(header, pn.pane.HTML)
    assert "MySample" in header.object
