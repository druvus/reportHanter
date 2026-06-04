"""Unit tests for the Dashboard landing section and supporting helpers."""

from __future__ import annotations

import pandas as pd
import pytest

from reporthanter.core.config import DefaultConfig
from reporthanter.processors.blast_processor import BlastProcessor
from reporthanter.report.dashboard import DashboardSection


@pytest.fixture
def blast_processor() -> BlastProcessor:
    return BlastProcessor(DefaultConfig().get_config("blast"))


@pytest.fixture
def dashboard_section() -> DashboardSection:
    return DashboardSection(DefaultConfig())


@pytest.mark.parametrize(
    "frame,n,expected_match_names,expected_contigs,expected_bp",
    [
        pytest.param(
            pd.DataFrame(
                {
                    "match_name": ["A", "A", "B", "C", "C", "C"],
                    "read_len": [1000, 2000, 500, 100, 100, 100],
                }
            ),
            3,
            ["A", "B", "C"],
            [2, 1, 3],
            [3000, 500, 300],
            id="ranks-by-cumulative-bp",
        ),
        pytest.param(
            pd.DataFrame({"match_name": ["A", "A", "B"]}),
            2,
            ["A", "B"],
            [2, 1],
            None,
            id="falls-back-to-count-without-read-len",
        ),
    ],
)
def test_top_matches_by_bp(
    blast_processor, frame, n, expected_match_names, expected_contigs, expected_bp
):
    top = blast_processor.top_matches_by_bp(frame, n=n)
    assert list(top["match_name"]) == expected_match_names
    assert list(top["contigs"]) == expected_contigs
    if expected_bp is not None:
        assert list(top["cumulative_bp"]) == expected_bp


def test_top_matches_by_bp_empty_frame_returns_empty(blast_processor):
    out = blast_processor.top_matches_by_bp(pd.DataFrame())
    assert out.empty
    assert list(out.columns) == ["match_name", "contigs", "cumulative_bp"]


def test_dashboard_section_renders_with_fixtures(dashboard_section, dashboard_kwargs):
    col = dashboard_section.generate_section(**dashboard_kwargs)
    # Header + sample band + KPI row + Divider + heading + top-hits row
    # + Divider + heading + assembly + Divider + heading + coverage = 12.
    # Don't pin the exact count; just confirm we got the canonical
    # Panel shape with enough top-level blocks for the landing card.
    assert hasattr(col, "objects")
    assert len(col.objects) >= 8


def test_dashboard_section_handles_missing_blast(dashboard_section, dashboard_kwargs):
    col = dashboard_section.generate_section(**{**dashboard_kwargs, "blastn_files": []})
    assert hasattr(col, "objects")
