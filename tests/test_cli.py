"""End-to-end CLI smoke test.

Drives the `reporthanter` console script against the canned fixtures and
confirms an HTML file is produced. Invokes the CLI as ``python -m
reporthanter.panel_report_cli`` so the test runs whether or not the
``reporthanter`` console-script wrapper is on the active PATH. This is the
only test that exercises the CLI wiring + ReportGenerator + every section
in one shot.
"""
from pathlib import Path
import subprocess
import sys

import pytest


FIXTURES = Path(__file__).parent / "fixtures"


def test_cli_produces_html(tmp_path):
    output = tmp_path / "report.html"

    completed = subprocess.run(
        [
            sys.executable, "-m", "reporthanter.panel_report_cli",
            "--blastn_file", str(FIXTURES / "blastn.csv"),
            "--kraken_file", str(FIXTURES / "kraken.tsv"),
            "--kaiju_table", str(FIXTURES / "kaiju.tsv"),
            "--fastp_json", str(FIXTURES / "fastp.json"),
            "--flagstat_file", str(FIXTURES / "flagstat.txt"),
            "--mosdepth_regions", str(FIXTURES / "mosdepth_regions.bed.gz"),
            "--output", str(output),
            "--sample_name", "smoke_test",
        ],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, (
        f"reporthanter exited with {completed.returncode}\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
    assert output.exists()
    assert output.stat().st_size > 10_000

    html = output.read_text(errors="ignore")
    assert "smoke_test" in html
    assert "Alignment" in html
