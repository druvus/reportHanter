"""End-to-end CLI smoke test.

Drives the `reporthanter` console script against the canned fixtures and
confirms an HTML file is produced. Invokes the CLI as ``python -m
reporthanter.panel_report_cli`` so the test runs whether or not the
``reporthanter`` console-script wrapper is on the active PATH. This is the
only test that exercises the CLI wiring + ReportGenerator + every section
in one shot.
"""

import subprocess
import sys
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def _cli_args(output: Path, **overrides) -> list[str]:
    """Build a CLI invocation against the canned fixtures.

    ``overrides`` replaces individual fixture paths (e.g. ``fastp_json=...``)
    so a test can swap one good input for a malformed one.
    """
    paths = {
        "blastn_file": FIXTURES / "blastn.csv",
        "kraken_file": FIXTURES / "kraken.tsv",
        "kaiju_table": FIXTURES / "kaiju.tsv",
        "fastp_json": FIXTURES / "fastp.json",
        "flagstat_file": FIXTURES / "flagstat.txt",
        "mosdepth_regions": FIXTURES / "mosdepth_regions.bed.gz",
    }
    paths.update(overrides)
    args = [sys.executable, "-m", "reporthanter.panel_report_cli"]
    for flag, path in paths.items():
        args += [f"--{flag}", str(path)]
    args += ["--output", str(output)]
    return args


def test_validate_only_passes_and_writes_no_report(tmp_path):
    output = tmp_path / "report.html"
    completed = subprocess.run(
        _cli_args(output) + ["--validate_only"],
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    # --validate_only must not produce a report.
    assert not output.exists()


def test_validate_only_rejects_malformed_content(tmp_path):
    # A present-but-corrupt fastp JSON passes the existence/size checks
    # but must be caught by content validation.
    bad_fastp = tmp_path / "bad_fastp.json"
    bad_fastp.write_text("{ this is not valid json")
    output = tmp_path / "report.html"

    completed = subprocess.run(
        _cli_args(output, fastp_json=bad_fastp) + ["--validate_only"],
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1
    assert not output.exists()
    assert "could not be parsed" in (completed.stdout + completed.stderr)


def test_cli_produces_html(tmp_path):
    output = tmp_path / "report.html"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "reporthanter.panel_report_cli",
            "--blastn_file",
            str(FIXTURES / "blastn.csv"),
            "--kraken_file",
            str(FIXTURES / "kraken.tsv"),
            "--kaiju_table",
            str(FIXTURES / "kaiju.tsv"),
            "--fastp_json",
            str(FIXTURES / "fastp.json"),
            "--flagstat_file",
            str(FIXTURES / "flagstat.txt"),
            "--mosdepth_regions",
            str(FIXTURES / "mosdepth_regions.bed.gz"),
            "--output",
            str(output),
            "--sample_name",
            "smoke_test",
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
