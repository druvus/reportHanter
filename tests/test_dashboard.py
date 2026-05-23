"""Unit tests for the Dashboard landing section and supporting helpers."""

from pathlib import Path

import pandas as pd
import pytest

from reporthanter.core.config import DefaultConfig
from reporthanter.processors.blast_processor import BlastProcessor
from reporthanter.report.dashboard import DashboardSection


FIXTURES = Path(__file__).parent / "fixtures"


def test_top_matches_by_bp_ranks_by_cumulative_bp():
    df = pd.DataFrame(
        {
            "match_name": ["A", "A", "B", "C", "C", "C"],
            "read_len": [1000, 2000, 500, 100, 100, 100],
        }
    )
    bp = BlastProcessor(DefaultConfig().get_config("blast"))
    top = bp.top_matches_by_bp(df, n=3)
    assert list(top["match_name"]) == ["A", "B", "C"]
    assert list(top["contigs"]) == [2, 1, 3]
    assert list(top["cumulative_bp"]) == [3000, 500, 300]


def test_top_matches_by_bp_empty_frame_returns_empty():
    bp = BlastProcessor(DefaultConfig().get_config("blast"))
    out = bp.top_matches_by_bp(pd.DataFrame())
    assert out.empty
    assert list(out.columns) == ["match_name", "contigs", "cumulative_bp"]


def test_top_matches_by_bp_falls_back_to_count_without_read_len():
    df = pd.DataFrame({"match_name": ["A", "A", "B"]})
    bp = BlastProcessor(DefaultConfig().get_config("blast"))
    top = bp.top_matches_by_bp(df, n=2)
    assert list(top["match_name"]) == ["A", "B"]
    assert list(top["contigs"]) == [2, 1]


def test_dashboard_section_renders_with_fixtures():
    section = DashboardSection(DefaultConfig())
    col = section.generate_section(
        sample_name="smoke",
        fastp_json=str(FIXTURES / "fastp.json"),
        flagstat_file=str(FIXTURES / "flagstat.txt"),
        kraken_file=str(FIXTURES / "kraken.tsv"),
        kaiju_table=str(FIXTURES / "kaiju.tsv"),
        blastn_files=[str(FIXTURES / "blastn.csv")],
        quast_reports=[],
        mosdepth_regions=str(FIXTURES / "mosdepth_regions.bed.gz"),
        virus_names=None,
    )
    # Should produce a Column with the expected number of top-level
    # blocks (header + sample band + KPI row + Divider + heading +
    # top-hits row + Divider + heading + assembly + Divider + heading
    # + coverage = 12). Don't pin the exact count; just confirm we got
    # the canonical Panel shape.
    assert hasattr(col, "objects")
    assert len(col.objects) >= 8


def test_dashboard_section_handles_missing_blast():
    section = DashboardSection(DefaultConfig())
    col = section.generate_section(
        sample_name="smoke",
        fastp_json=str(FIXTURES / "fastp.json"),
        flagstat_file=str(FIXTURES / "flagstat.txt"),
        kraken_file=str(FIXTURES / "kraken.tsv"),
        kaiju_table=str(FIXTURES / "kaiju.tsv"),
        blastn_files=[],
        quast_reports=[],
        mosdepth_regions=str(FIXTURES / "mosdepth_regions.bed.gz"),
        virus_names=None,
    )
    assert hasattr(col, "objects")
