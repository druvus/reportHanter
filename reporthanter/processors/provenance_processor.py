"""Provenance processor.

Loads the per-run provenance sidecar that virusHanter2 writes
(``run_provenance_<batch>.json``) into small tables the report renders:
which reference databases (with a build identity, not a fragile mtime)
and which resolved tool versions produced the run. The processor only
parses -- the pipeline is the single source of truth -- and never shows
an absolute path: the sidecar already carries short ``folder/leaf`` paths.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from ..core.config import DefaultConfig


class ProvenanceProcessor:
    """Parse the provenance sidecar into database / software tables."""

    def __init__(self, config: dict[str, Any] | DefaultConfig | None = None) -> None:
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    def load(self, path: str | Path) -> dict[str, Any]:
        """Load the sidecar JSON, returning an empty mapping on failure.

        The section degrades to a "not recorded" note rather than
        failing the whole report when the file is absent or malformed.
        """
        p = Path(path)
        if not p.is_file():
            return {}
        try:
            with p.open() as fh:
                data = json.load(fh)
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError) as exc:
            self.logger.warning(f"Could not read provenance sidecar {p}: {exc}")
            return {}

    def databases_frame(self, data: dict[str, Any]) -> pd.DataFrame:
        """Return a Database / Snapshot / Date / Path table.

        ``Snapshot`` is the robust build identity (e.g. ``checkv-db-v1.5``
        or the refresh build_stats source+date); ``Path`` is the short
        ``folder/leaf`` the sidecar recorded -- never an absolute path.
        """
        rows = []
        for db in data.get("databases", []):
            rows.append(
                {
                    "Database": db.get("key", ""),
                    "Snapshot": db.get("identity", ""),
                    "Date": db.get("date", ""),
                    "Path": db.get("path", ""),
                }
            )
        return pd.DataFrame(rows, columns=["Database", "Snapshot", "Date", "Path"])

    def software_frame(self, data: dict[str, Any]) -> pd.DataFrame:
        """Return a Tool / Version table of the resolved headline tools."""
        headline = data.get("software_headline", {})
        rows = [{"Tool": tool, "Version": version} for tool, version in sorted(headline.items())]
        return pd.DataFrame(rows, columns=["Tool", "Version"])

    def run_frame(self, data: dict[str, Any]) -> pd.DataFrame:
        """Return a Field / Value table of the run-level scalars."""
        assemblers = data.get("assemblers_used", [])
        rows = [
            ("Run", data.get("run_name", "")),
            ("Generated (UTC)", data.get("generated_utc", "")),
            ("Host removal", data.get("host_removal_tool", "")),
            ("Assemblers", ", ".join(assemblers) if assemblers else ""),
            ("reportHanter", data.get("reporthanter_version", "")),
            ("Snakemake", data.get("snakemake_version", "")),
            ("Python (driver)", data.get("python_version", "")),
        ]
        return pd.DataFrame([{"Field": f, "Value": v} for f, v in rows], columns=["Field", "Value"])
