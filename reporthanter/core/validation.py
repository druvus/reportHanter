"""
Shared input-file validation for reportHanter.

Used by both the CLI entry point and the public ``create_report``
wrapper so that file presence and readability checks run regardless
of how the caller invokes the package.
"""

import logging
from collections.abc import Sequence
from pathlib import Path

from .exceptions import ConfigurationError

_logger = logging.getLogger(__name__)


def _check_file(
    name: str,
    path: str | Path,
    require_nonempty: bool = True,
) -> list[str]:
    """Return a list of error strings for a single file path.

    Checks existence, regular-file status, and (when
    ``require_nonempty=True``) non-zero size.  Returns an empty
    list when all checks pass.
    """
    errors: list[str] = []
    fp = Path(path)
    if not fp.exists():
        errors.append(f"{name} does not exist: {path}")
    elif not fp.is_file():
        errors.append(f"{name} is not a regular file: {path}")
    elif require_nonempty and fp.stat().st_size == 0:
        errors.append(f"{name} is empty: {path}")
    return errors


def validate_report_inputs(
    kraken_file: str | Path,
    kaiju_table: str | Path,
    fastp_json: str | Path,
    flagstat_file: str | Path,
    mosdepth_regions: str | Path,
    blastn_files: Sequence[str | Path] | None = None,
    secondary_flagstat_file: str | Path | None = None,
    virus_names: str | Path | None = None,
    quast_reports: Sequence[str | Path] | None = None,
    genomad_summaries: Sequence[str | Path] | None = None,
) -> None:
    """Validate that all supplied input files exist and are readable.

    .. rubric:: Empty-file contract

    The following files must exist **and** be non-empty; a zero-byte
    file raises :exc:`~reporthanter.core.exceptions.ConfigurationError`
    with a clear message naming the offending path:

    * Kraken TSV (required, non-empty)
    * Kaiju TSV (required, non-empty)
    * FastP JSON (required, non-empty)
    * Flagstat file (required, non-empty)
    * Mosdepth regions BED/BED.GZ (required, non-empty)

    BLAST CSVs are the one exception: an empty CSV simply indicates that
    the upstream assembler produced no contigs for this sample.  The
    report still renders with an empty contig table.  At least one BLAST
    path must be supplied, but the file itself may be zero bytes.

    Optional inputs (secondary flagstat, virus names TSV, QUAST reports,
    geNomad summaries) are checked for existence and non-empty size only
    when they are provided.

    Raises :exc:`~reporthanter.core.exceptions.ConfigurationError`
    listing all violations found.  Each violation is also logged at
    ``ERROR`` level so callers that catch the exception still see the
    individual messages in the log stream.
    """
    errors: list[str] = []

    # Required singleton inputs (non-empty).
    for name, path in (
        ("Kraken file", kraken_file),
        ("Kaiju table", kaiju_table),
        ("FastP JSON", fastp_json),
        ("Flagstat file", flagstat_file),
        ("Mosdepth regions file", mosdepth_regions),
    ):
        errors.extend(_check_file(name, path))

    # BLAST CSVs: at least one required; empty files are tolerated.
    blast_paths = list(blastn_files or [])
    if not blast_paths:
        errors.append(
            "At least one BLAST CSV is required (supply blastn_files=[...] or blastn_file=...)."
        )
    for path in blast_paths:
        errors.extend(_check_file("BLAST CSV", path, require_nonempty=False))

    # Optional singleton files (non-empty when provided).
    if secondary_flagstat_file:
        errors.extend(_check_file("Secondary flagstat file", secondary_flagstat_file))
    if virus_names:
        errors.extend(_check_file("Virus names TSV", virus_names))

    # Optional list inputs (non-empty when provided).
    for path in quast_reports or []:
        errors.extend(_check_file("QUAST report", path))
    for path in genomad_summaries or []:
        errors.extend(_check_file("geNomad summary", path))

    if errors:
        for error in errors:
            _logger.error(error)
        raise ConfigurationError(
            f"Input validation failed with {len(errors)} error(s); "
            "see the log output above for details."
        )
