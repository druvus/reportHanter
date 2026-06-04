"""Tests for the pure-Python helper functions in report/sections.py.

These helpers are separated from the Panel/Altair widget builders so
they can be unit-tested without a running Panel server.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from reporthanter.report.sections import (
    _apply_canonical_blast_names,
    _blast_header_filters,
    _coverage_header_filters,
    _coverage_summary_frame,
)

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# _blast_header_filters
# ---------------------------------------------------------------------------


def test_blast_header_filters_known_columns():
    cols = ["match_name", "percent_identity", "read_len", "accession", "assembler", "provirus"]
    spec = _blast_header_filters(cols)
    assert "match_name" in spec
    assert spec["match_name"]["func"] == "like"
    assert "percent_identity" in spec
    assert spec["percent_identity"]["func"] == ">="
    assert "assembler" in spec
    assert "provirus" in spec


def test_blast_header_filters_unknown_columns_skipped():
    spec = _blast_header_filters(["nonexistent_column"])
    assert "nonexistent_column" not in spec


def test_blast_header_filters_empty_columns():
    spec = _blast_header_filters([])
    assert spec == {}


# ---------------------------------------------------------------------------
# _coverage_header_filters
# ---------------------------------------------------------------------------


def test_coverage_header_filters_numeric_columns():
    cols = ["chrom", "species", "length", "mean_depth", "pct_ge_5x", "pct_ge_10x"]
    spec = _coverage_header_filters(cols)
    assert spec["length"]["func"] == ">="
    assert spec["mean_depth"]["func"] == ">="
    assert spec["chrom"]["func"] == "like"
    assert spec["species"]["func"] == "like"


def test_coverage_header_filters_subset_of_columns():
    spec = _coverage_header_filters(["chrom", "pct_ge_10x"])
    assert "chrom" in spec
    assert "pct_ge_10x" in spec
    assert "mean_depth" not in spec


# ---------------------------------------------------------------------------
# _coverage_summary_frame
# ---------------------------------------------------------------------------


def _make_coverage_df():
    """Small mosdepth-like regions DataFrame for testing."""
    return pd.DataFrame(
        {
            "chrom": ["NC_001", "NC_001", "NC_001", "NC_002", "NC_002"],
            "start": [0, 100, 200, 0, 100],
            "end": [100, 200, 300, 100, 200],
            "depth": [15.0, 8.0, 3.0, 30.0, 25.0],
        }
    )


def test_coverage_summary_frame_columns():
    df = _make_coverage_df()
    summary = _coverage_summary_frame(df, {}, {})
    expected_cols = {
        "chrom",
        "species",
        "aliases",
        "sources",
        "length",
        "mean_depth",
        "pct_ge_5x",
        "pct_ge_10x",
    }
    assert expected_cols.issubset(set(summary.columns))


def test_coverage_summary_frame_sorted_by_pct_ge_10x():
    df = _make_coverage_df()
    summary = _coverage_summary_frame(df, {}, {})
    # NC_002 has 100% at >= 10x; NC_001 has only 1/3 windows at >= 10x
    assert summary.iloc[0]["chrom"] == "NC_002"


def test_coverage_summary_frame_empty_df_returns_empty():
    summary = _coverage_summary_frame(pd.DataFrame(), {}, {})
    assert summary.empty


def test_coverage_summary_frame_no_depth_column():
    df = pd.DataFrame({"chrom": ["NC_001"], "start": [0], "end": [100]})
    summary = _coverage_summary_frame(df, {}, {})
    assert summary.empty


def test_coverage_summary_frame_name_lookup():
    df = _make_coverage_df()
    name_map = {"NC_001": "Herpesvirus", "NC_002": "Adenovirus"}
    summary = _coverage_summary_frame(df, name_map, {})
    nc2 = summary.loc[summary["chrom"] == "NC_002"].iloc[0]
    assert nc2["species"] == "Adenovirus"


def test_coverage_summary_frame_aliases():
    df = _make_coverage_df()
    alias_map = {"NC_001": "HHV-1"}
    summary = _coverage_summary_frame(df, {}, {}, chrom_to_aliases=alias_map)
    nc1 = summary.loc[summary["chrom"] == "NC_001"].iloc[0]
    assert nc1["aliases"] == "HHV-1"


# ---------------------------------------------------------------------------
# _apply_canonical_blast_names
# ---------------------------------------------------------------------------


def _blast_data():
    return pd.DataFrame(
        {
            "match_name": ["OldName_A", "OldName_B"],
            "accession": ["NC_001.1", "NC_003.2"],
        }
    )


def test_apply_canonical_blast_names_swaps_name(tmp_path):
    sidecar = tmp_path / "virus_names.tsv"
    sidecar.write_text("chrom\tname\nNC_001\tCanonical_A\nNC_003\tCanonical_B\n")
    df = _blast_data()
    result = _apply_canonical_blast_names(df, sidecar)
    assert result.loc[result["accession"] == "NC_001.1", "match_name"].iloc[0] == "Canonical_A"
    assert result.loc[result["accession"] == "NC_003.2", "match_name"].iloc[0] == "Canonical_B"


def test_apply_canonical_blast_names_pushes_old_name_to_aliases(tmp_path):
    sidecar = tmp_path / "virus_names.tsv"
    sidecar.write_text("chrom\tname\nNC_001\tCanonical_A\n")
    df = _blast_data()
    result = _apply_canonical_blast_names(df, sidecar)
    aliases = result.loc[result["accession"] == "NC_001.1", "aliases"].iloc[0]
    assert "OldName_A" in aliases


def test_apply_canonical_blast_names_no_sidecar():
    """When virus_names is None the frame is returned unchanged."""
    df = _blast_data()
    result = _apply_canonical_blast_names(df, None)
    assert result["match_name"].tolist() == df["match_name"].tolist()


def test_apply_canonical_blast_names_no_match():
    """When none of the accessions match, the frame is returned unchanged."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
        f.write("chrom\tname\nNC_999\tSomething\n")
        fname = f.name

    df = _blast_data()
    result = _apply_canonical_blast_names(df, fname)
    assert result["match_name"].tolist() == df["match_name"].tolist()


def test_apply_canonical_blast_names_missing_required_columns():
    """Missing chrom or name column returns the frame unchanged."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
        f.write("chrom\ttaxid\nNC_001\t12345\n")  # no 'name' column
        fname = f.name

    df = _blast_data()
    result = _apply_canonical_blast_names(df, fname)
    assert result["match_name"].tolist() == df["match_name"].tolist()


def test_apply_canonical_blast_names_empty_frame(tmp_path):
    sidecar = tmp_path / "virus_names.tsv"
    sidecar.write_text("chrom\tname\nNC_001\tCanonical_A\n")
    result = _apply_canonical_blast_names(pd.DataFrame(), sidecar)
    assert result.empty
