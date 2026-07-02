"""Tests for KaijuProcessor."""

from pathlib import Path

import pandas as pd
import pytest

from reporthanter.core.exceptions import DataProcessingError
from reporthanter.processors.kaiju_processor import KaijuProcessor

FIXTURES = Path(__file__).parent / "fixtures"


def test_empty_kaiju_file_is_tolerated(tmp_path):
    # A sample with zero reads reaching Kaiju can leave a 0-byte table;
    # validate + process must not raise, and filter_data must return an
    # empty frame + 0.0 so the Classification tab renders a placeholder.
    empty = tmp_path / "empty.kaiju.tsv"
    empty.touch()
    proc = KaijuProcessor()

    assert proc.validate_input(empty) is True
    df = proc.process(str(empty))
    assert df.empty
    assert {"percent", "taxon_name"}.issubset(df.columns)
    # `percent` must be numeric even when empty: the Dashboard does
    # (percent * 100).round(2), which raises on an object dtype (pandas 2.x).
    assert df["percent"].dtype.kind == "f"

    filtered, unclassified_pct = proc.filter_data(df, cutoff=0.01, max_entries=10)
    assert filtered.empty
    assert unclassified_pct == 0.0


def test_process_normalizes_percent_to_fraction():
    proc = KaijuProcessor()
    df = proc.process(str(FIXTURES / "kaiju.tsv"))

    # The fixture has 40% unclassified -> 0.40 after /100.
    unclassified = df.loc[df.taxon_name == "unclassified", "percent"].iloc[0]
    assert unclassified == pytest.approx(0.40)


def test_filter_data_excludes_unclassified_and_applies_cutoff():
    proc = KaijuProcessor()
    df = proc.process(str(FIXTURES / "kaiju.tsv"))

    filtered, unclassified_pct = proc.filter_data(df, cutoff=0.01, max_entries=10)

    assert unclassified_pct == pytest.approx(0.40)
    assert "unclassified" not in filtered.taxon_name.tolist()
    # BelowCutoff row at 0.001 fraction should be dropped.
    assert "BelowCutoff" not in filtered.taxon_name.tolist()


def test_filter_data_respects_max_entries():
    proc = KaijuProcessor()
    df = proc.process(str(FIXTURES / "kaiju.tsv"))

    filtered, _ = proc.filter_data(df, cutoff=0.0, max_entries=2)
    assert len(filtered) == 2


def test_validate_rejects_missing_columns(tmp_path):
    bogus = tmp_path / "kaiju.tsv"
    bogus.write_text("foo\tbar\n1\t2\n")

    proc = KaijuProcessor()
    with pytest.raises(DataProcessingError):
        proc.validate_input(bogus)


def test_filter_data_empty_dataframe_returns_empty_and_zero():
    """filter_data on an empty DataFrame must not raise IndexError.

    An empty Kaiju table is not expected in normal runs, but the guard
    must degrade gracefully rather than propagating a raw IndexError.
    """
    proc = KaijuProcessor()
    empty = pd.DataFrame(columns=["percent", "reads", "taxon_id", "taxon_name"])
    filtered, unclassified_pct = proc.filter_data(empty, cutoff=0.0)

    assert filtered.empty
    assert unclassified_pct == 0.0


def test_filter_data_no_unclassified_row_returns_zero():
    """filter_data returns unclassified_pct=0.0 when no 'unclassified' row is present."""
    proc = KaijuProcessor()
    data = pd.DataFrame(
        {
            "percent": [0.30, 0.15],
            "reads": [300, 150],
            "taxon_id": [10239, 2],
            "taxon_name": ["Viruses", "Bacteria"],
        }
    )
    _, unclassified_pct = proc.filter_data(data, cutoff=0.0)
    assert unclassified_pct == 0.0


def test_find_database_files_missing_fmi(tmp_path):
    """find_database_files raises DataProcessingError when .fmi is absent."""
    (tmp_path / "names.dmp").write_text("")
    (tmp_path / "nodes.dmp").write_text("")

    with pytest.raises(DataProcessingError, match=r"\.fmi"):
        KaijuProcessor.find_database_files(tmp_path)


def test_find_database_files_missing_names(tmp_path):
    """find_database_files raises DataProcessingError when names.dmp is absent."""
    (tmp_path / "db.fmi").write_text("")
    (tmp_path / "nodes.dmp").write_text("")

    with pytest.raises(DataProcessingError, match="names.dmp"):
        KaijuProcessor.find_database_files(tmp_path)


def test_find_database_files_missing_nodes(tmp_path):
    """find_database_files raises DataProcessingError when nodes.dmp is absent."""
    (tmp_path / "db.fmi").write_text("")
    (tmp_path / "names.dmp").write_text("")

    with pytest.raises(DataProcessingError, match="nodes.dmp"):
        KaijuProcessor.find_database_files(tmp_path)
