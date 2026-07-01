"""Tests for the provenance processor.

The processor parses the run provenance sidecar into database / software
tables for the report's Provenance tab, degrades gracefully when the
sidecar is absent, and never surfaces an absolute path.
"""

from __future__ import annotations

import json
from pathlib import Path

from reporthanter.processors.provenance_processor import ProvenanceProcessor

_SIDECAR = {
    "run_name": "20260101_batch",
    "generated_utc": "2026-07-01T15:00:00Z",
    "host_removal_tool": "bwa",
    "assemblers_used": ["MEGAHIT", "metaSPAdes"],
    "reporthanter_version": "v0.9.0",
    "snakemake_version": "9.23.1",
    "python_version": "3.12.2",
    "databases": [
        {
            "key": "CHECKV_DB",
            "path": "checkv/checkv-db-v1.5",
            "identity": "checkv-db-v1.5",
            "date": "2024-01-10",
        },
        {
            "key": "VIRUS_PARQUET",
            "path": "virus_ref/all_viruses.parquet",
            "identity": "refseq 2026-05-17 (14899 refs)",
            "date": "2026-05-17",
        },
    ],
    "software": [{"env": "fastp", "package": "fastp", "version": "0.24.0", "build": "b0"}],
    "software_headline": {"fastp": "0.24.0", "kraken2": "2.1.3"},
}


def _write(tmp_path: Path) -> Path:
    p = tmp_path / "run_provenance_20260101_batch.json"
    p.write_text(json.dumps(_SIDECAR))
    return p


def test_load_missing_returns_empty(tmp_path):
    proc = ProvenanceProcessor()
    assert proc.load(tmp_path / "absent.json") == {}


def test_databases_frame(tmp_path):
    proc = ProvenanceProcessor()
    data = proc.load(_write(tmp_path))
    df = proc.databases_frame(data)
    assert list(df.columns) == ["Database", "Snapshot", "Date", "Path"]
    checkv = df[df["Database"] == "CHECKV_DB"].iloc[0]
    assert checkv["Snapshot"] == "checkv-db-v1.5"
    # Short path only; no absolute path leaks.
    assert checkv["Path"] == "checkv/checkv-db-v1.5"
    assert not df["Path"].str.startswith("/").any()


def test_software_frame_is_headline_sorted(tmp_path):
    proc = ProvenanceProcessor()
    data = proc.load(_write(tmp_path))
    df = proc.software_frame(data)
    assert list(df.columns) == ["Tool", "Version"]
    assert df.iloc[0]["Tool"] == "fastp"
    assert df.iloc[0]["Version"] == "0.24.0"
    assert set(df["Tool"]) == {"fastp", "kraken2"}


def test_run_frame_carries_scalars(tmp_path):
    proc = ProvenanceProcessor()
    data = proc.load(_write(tmp_path))
    df = proc.run_frame(data)
    lookup = dict(zip(df["Field"], df["Value"], strict=True))
    assert lookup["Host removal"] == "bwa"
    assert lookup["Assemblers"] == "MEGAHIT, metaSPAdes"
    assert lookup["reportHanter"] == "v0.9.0"


def test_frames_empty_on_missing_sidecar():
    proc = ProvenanceProcessor()
    data: dict = {}
    assert proc.databases_frame(data).empty
    assert proc.software_frame(data).empty
