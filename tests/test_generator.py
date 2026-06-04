"""Unit tests for ReportGenerator utility methods.

These tests exercise the helper methods that do not require building a full
Panel layout, so they run quickly without launching a Panel server.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from reporthanter.core.config import DefaultConfig
from reporthanter.report.generator import ReportGenerator


@pytest.fixture
def generator():
    return ReportGenerator(DefaultConfig())


# ---------------------------------------------------------------------------
# _coalesce_paths
# ---------------------------------------------------------------------------


def test_coalesce_paths_list_only():
    result = ReportGenerator._coalesce_paths(["a.csv", "b.csv"], None)
    assert result == [Path("a.csv"), Path("b.csv")]


def test_coalesce_paths_singular_only():
    result = ReportGenerator._coalesce_paths(None, "single.csv")
    assert result == [Path("single.csv")]


def test_coalesce_paths_both():
    result = ReportGenerator._coalesce_paths(["a.csv"], "b.csv")
    assert result == [Path("a.csv"), Path("b.csv")]


def test_coalesce_paths_both_none():
    result = ReportGenerator._coalesce_paths(None, None)
    assert result == []


def test_coalesce_paths_filters_empty_strings():
    result = ReportGenerator._coalesce_paths(["", "a.csv"], None)
    assert result == [Path("a.csv")]


# ---------------------------------------------------------------------------
# _logo_data_uri
# ---------------------------------------------------------------------------


def test_logo_data_uri_returns_string(generator):
    uri = generator._logo_data_uri()
    # Either a valid base64 data URI or an empty string (asset not packaged).
    assert isinstance(uri, str)
    if uri:
        assert uri.startswith("data:image/png;base64,")


# ---------------------------------------------------------------------------
# _build_section — error propagation
# ---------------------------------------------------------------------------


def test_build_section_wraps_exception(generator):
    from reporthanter.core.exceptions import ReportGenerationError

    def _failing_builder(**kwargs):
        raise ValueError("synthetic failure")

    with pytest.raises(ReportGenerationError, match="synthetic failure"):
        generator._build_section("TestSection", _failing_builder)


def test_build_section_passes_kwargs(generator):
    received = {}

    def _capture_builder(**kwargs):
        received.update(kwargs)
        return "ok"

    result = generator._build_section("Cap", _capture_builder, sample_name="S1")
    assert result == "ok"
    assert received["sample_name"] == "S1"
