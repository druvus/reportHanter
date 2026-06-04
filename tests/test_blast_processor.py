"""Tests for BlastProcessor and BlastPlotGenerator (no subprocess invocation)."""

from pathlib import Path

import pandas as pd
import pytest

from reporthanter.core.exceptions import DataProcessingError, FileValidationError
from reporthanter.processors.blast_processor import BlastPlotGenerator, BlastProcessor

FIXTURES = Path(__file__).parent / "fixtures"


def test_process_reads_csv_unchanged():
    proc = BlastProcessor()
    df = proc.process(str(FIXTURES / "blastn.csv"))

    assert {"name", "match_name", "accession", "percent_identity"}.issubset(df.columns)
    assert len(df) == 3


def test_validate_accepts_well_formed_csv():
    proc = BlastProcessor()
    assert proc.validate_input(FIXTURES / "blastn.csv") is True


def test_validate_rejects_missing_file(tmp_path):
    proc = BlastProcessor()
    with pytest.raises((FileValidationError, DataProcessingError)):
        proc.validate_input(tmp_path / "does_not_exist.csv")


def test_empty_csv_round_trips(tmp_path):
    empty = tmp_path / "empty.csv"
    pd.DataFrame(columns=["name", "match_name"]).to_csv(empty, index=False)

    proc = BlastProcessor()
    df = proc.process(str(empty))
    assert df.empty
    assert list(df.columns) == ["name", "match_name"]


# ---------------------------------------------------------------------------
# top_matches_by_bp
# ---------------------------------------------------------------------------


def _blast_frame(**kwargs):
    """Build a minimal BLAST-like DataFrame for unit tests."""
    defaults = {
        "match_name": ["Herpes", "Herpes", "Adeno", "Adeno", "Adeno"],
        "read_len": [5000, 3000, 1000, 2000, 500],
        "accession": ["NC_001", "NC_001", "NC_002", "NC_002", "NC_002"],
    }
    defaults.update(kwargs)
    return pd.DataFrame(defaults)


def test_top_matches_by_bp_sums_correctly():
    proc = BlastProcessor()
    frame = _blast_frame()
    top = proc.top_matches_by_bp(frame, n=10)
    assert len(top) == 2
    herpes_row = top.loc[top["match_name"] == "Herpes"].iloc[0]
    assert herpes_row["cumulative_bp"] == 8000
    adeno_row = top.loc[top["match_name"] == "Adeno"].iloc[0]
    assert adeno_row["cumulative_bp"] == 3500


def test_top_matches_by_bp_limits_to_n():
    proc = BlastProcessor()
    frame = _blast_frame()
    top = proc.top_matches_by_bp(frame, n=1)
    assert len(top) == 1
    # Herpes has more bp than Adeno
    assert top.iloc[0]["match_name"] == "Herpes"


def test_top_matches_by_bp_empty_input():
    proc = BlastProcessor()
    top = proc.top_matches_by_bp(pd.DataFrame(), n=5)
    assert top.empty
    assert list(top.columns) == ["match_name", "contigs", "cumulative_bp"]


def test_top_matches_by_bp_no_match_name_column():
    proc = BlastProcessor()
    top = proc.top_matches_by_bp(pd.DataFrame({"accession": ["NC_001"]}), n=5)
    assert top.empty


def test_top_matches_by_bp_carries_aliases():
    proc = BlastProcessor()
    frame = _blast_frame()
    frame["aliases"] = ["alias_H", "alias_H", "alias_A", "alias_A", "alias_A"]
    top = proc.top_matches_by_bp(frame, n=10)
    assert "aliases" in top.columns
    herpes_alias = top.loc[top["match_name"] == "Herpes", "aliases"].iloc[0]
    assert herpes_alias == "alias_H"


def test_top_matches_by_bp_fallback_to_count_when_no_bp():
    """When read_len is absent, ranking falls back to contig count."""
    proc = BlastProcessor()
    frame = pd.DataFrame(
        {
            "match_name": ["Herpes", "Adeno", "Adeno", "Adeno"],
        }
    )
    top = proc.top_matches_by_bp(frame, n=5)
    assert top.iloc[0]["match_name"] == "Adeno"


# ---------------------------------------------------------------------------
# BlastPlotGenerator - chart generation
# ---------------------------------------------------------------------------


def test_blast_plot_generator_single_assembler():
    gen = BlastPlotGenerator()
    frame = _blast_frame()
    chart = gen.generate_plot(frame)
    assert chart is not None


def test_blast_plot_generator_multi_assembler():
    gen = BlastPlotGenerator()
    frame = _blast_frame()
    frame["assembler"] = ["MEGAHIT", "MEGAHIT", "metaSPAdes", "metaSPAdes", "metaSPAdes"]
    chart = gen.generate_plot(frame)
    assert chart is not None


def test_blast_plot_generator_empty_data():
    gen = BlastPlotGenerator()
    chart = gen.generate_plot(pd.DataFrame())
    assert chart is not None


def test_create_bp_chart_returns_chart():
    gen = BlastPlotGenerator()
    frame = _blast_frame()
    chart = gen.create_bp_chart(frame)
    assert chart is not None


def test_create_bp_chart_missing_columns_returns_empty():
    gen = BlastPlotGenerator()
    # No read_len column
    frame = pd.DataFrame({"match_name": ["Herpes"]})
    chart = gen.create_bp_chart(frame)
    assert chart is not None


def test_create_bp_chart_multi_assembler():
    gen = BlastPlotGenerator()
    frame = _blast_frame()
    frame["assembler"] = ["MEGAHIT", "MEGAHIT", "metaSPAdes", "metaSPAdes", "metaSPAdes"]
    chart = gen.create_bp_chart(frame)
    assert chart is not None
