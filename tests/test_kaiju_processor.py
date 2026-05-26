"""Tests for KaijuProcessor."""
from pathlib import Path

import pytest

from reporthanter.core.exceptions import DataProcessingError
from reporthanter.processors.kaiju_processor import KaijuProcessor

FIXTURES = Path(__file__).parent / "fixtures"


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
