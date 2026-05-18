# Version 0.3.0 architecture summary

Version 0.3.0 removed the legacy free-function modules inherited
from the original `virusHanter` Snakefile and replaced them with a
processor-based architecture. This note records the resulting layout
and the migration paths that remain supported.

## Removed modules

The following modules and their public functions were deleted:

| Module | Functions removed |
|--------|-------------------|
| `kraken.py` | `wrangle_kraken`, `kraken_df`, `plot_kraken` |
| `kaiju.py` | `plot_kaiju`, `kaiju_db_files` |
| `blast.py` | `run_blastn`, `plot_blastn` |
| `flagstat.py` | `parse_bwa_flagstat`, `plot_flagstat`, `alignment_stats` |
| `fastp.py` | `parse_fastp_json`, `create_fastp_summary_table` |
| `file_utils.py` | `common_suffix`, `paired_reads` |
| `fastx.py` | `fastx_file_to_df` |
| `panel_report.py` | `panel_report` |

None of these names are re-exported from `reporthanter` in 0.3.0.
Importing them raises `ImportError`.

## Current public API

`reporthanter/__init__.py` exposes:

```python
from reporthanter import (
    # Report generation
    ReportGenerator,
    DefaultConfig,
    create_report,           # signature-compatible wrapper

    # Processors
    KrakenProcessor,
    KaijuProcessor,
    BlastProcessor,
    FastpProcessor,
    FlagstatProcessor,

    # Plot generators
    KrakenPlotGenerator,
    KaijuPlotGenerator,
    BlastPlotGenerator,

    # Exceptions
    ReportHanterError,
    DataProcessingError,
)
```

The CLI entry point `reporthanter` (defined in
`panel_report_cli.py`) is unchanged and remains the stable contract
with `virusHanter2`'s `generate_report` rule.

## Migration paths

### CLI

No changes. The flag set is the same as in 0.2.x.

### Python API

The simplest migration is to replace `panel_report` with
`create_report`:

```python
# 0.2.x
from reporthanter import panel_report
report = panel_report(blastn_file="...", kraken_file="...", ...)

# 0.3.x, minimal change
from reporthanter import create_report
report = create_report(blastn_file="...", kraken_file="...", ...)
```

For new code, prefer the explicit generator:

```python
from reporthanter import ReportGenerator, DefaultConfig

generator = ReportGenerator(DefaultConfig())
report = generator.generate_report(
    blastn_file="...", kraken_file="...", ...
)
```

## Package layout after 0.3.0

```
reporthanter/
  core/
    interfaces.py     Abstract base classes for processors
                      and plot generators
    exceptions.py     ReportHanterError and subclasses
    config.py         DefaultConfig and JSON loading
    base.py           Shared base implementations
  processors/
    kraken_processor.py
    kaiju_processor.py
    blast_processor.py
    fastp_processor.py
    flagstat_processor.py
  report/
    sections.py       Per-section layout helpers
    generator.py      ReportGenerator
  visualization/      Optional enhanced plotting layer
  panel_report_cli.py CLI entry point
  __init__.py         Public re-exports
```

Each processor owns parsing for one tool's output and exposes a
small interface; the matching plot generator owns the corresponding
Altair chart. `ReportGenerator` composes processors and section
helpers into the final Panel layout.

## Verification

Run `make all-checks` for the full developer workflow
(`ruff format-check`, `ruff check`, `mypy`, `pytest`).
`scripts/test_0_3_structure.py` provides an additional layout
sanity check that asserts the expected package structure and
that the legacy flat modules are absent.
