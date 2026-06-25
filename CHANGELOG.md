# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.0] - 2026-06-04

Robustness and quality hardening. Both public surfaces
(`create_report`, `ReportGenerator`) are preserved and the default
report output is unchanged.

### Added
- Shared input validation (`core/validation.py`) reused by both
  `create_report()` and the CLI, including fastp JSON structure
  checks.

### Changed
- Empty or malformed Kaiju / Kraken / flagstat inputs now raise a
  clear `DataProcessingError` instead of an `IndexError`.
- Broad `except Exception` sites replaced with specific exception
  types.
- Magic numbers (bar step height, the sub-1 % dashboard filter)
  moved into the configuration; the four `_apply_styling` overrides
  collapsed onto a single `PRESERVE_CHART_HEIGHT` base-class flag.
- `mypy` is now enforced as part of `make all-checks` (0 errors,
  previously 53); critical-path test coverage raised to 77 % (from
  45 %). Pre-commit configuration refreshed to ruff + mypy. Empty-file
  and threshold-precedence contracts documented.

## [0.8.11] - 2026-05-26

### Added
- `create_report()` gains a `primary_host` parameter.

### Changed
- `__version__` is read dynamically from the installed-package
  metadata so it tracks `pyproject.toml`. Test-suite tidy.

## [0.8.10] - 2026-05-26

### Changed
- Standardised the narrow bar styling across the Kraken, Kaiju,
  BLAST and Host alignment charts.

## [0.8.9] - 2026-05-25

### Changed
- Dashboard landing cards drop rows below 1 % of reads to reduce
  noise.

## [0.8.8] - 2026-05-25

### Changed
- Assembly classification layout polish.

## [0.8.7] - 2026-05-25

### Changed
- Surface the ICTV-canonical species names in the Dashboard and the
  contig table.

## [0.8.6] - 2026-05-25

### Fixed
- Host alignment: corrected bar height, surfaced the host name, and
  made the primary and secondary panels symmetric.

## [0.8.5] - 2026-05-25

### Changed
- Tab and banner alignment; dead-code purge; raw column-name
  handling.

## [0.8.4] - 2026-05-25

### Removed
- The broken "Download contig table as CSV" button.

## [0.8.3] - 2026-05-25

### Changed
- Dropped the header filters from the Dashboard tables.

## [0.8.2] - 2026-05-25

### Added
- Per-column header filters on the Coverage and Dashboard tables.

## [0.8.1] - 2026-05-25

### Added
- Per-column header filters on the BLAST contig table.

## [0.8.0] - 2026-05-25

### Added
- Light, brand-aligned report header with the embedded reportHanter
  wordmark.

## [0.7.0] - 2026-05-24

### Added
- "Also known as" column in the Dashboard top-5 Kraken / Kaiju /
  BLAST cards, the Best-covered references + Highest mean depth
  references tables and the Coverage section's summary table. The
  column is populated when the upstream pipeline (virusHanter2
  >= today's commit) supplies an `aliases` column carrying the
  legacy NCBI scientific name plus the non-scientific NCBI name
  categories (acronym, common name, equivalent name, synonym) for
  the row taxid and its species ancestor.
- `_coverage_summary_frame` gains an optional `chrom_to_aliases`
  argument so the alias column threads through the Coverage
  summary frame to both the main Coverage section and the
  Dashboard.

### Changed
- `BlastProcessor.top_matches_by_bp` propagates the `aliases`
  column through the group-by so the Dashboard BLAST card can
  surface legacy synonyms alongside the canonical match name.

## [0.6.3] - 2026-05-24

### Changed
- BLAST chart data and Tabulator views in the Assembly
  classification tab now ship only the columns the chart / table
  references. The raw BLAST stitle in `matches` and the
  audit-only `*_raw` columns the virusHanter2 canonicaliser keeps
  alongside the ICTV-binomial name no longer leak through the
  Vega data embed into the rendered HTML. `KaijuProcessor` strips
  `*_raw` columns at read time.

## [0.6.2] - 2026-05-23

### Fixed
- BLAST chart x-axis was clipped at the bottom because the chart
  asked for 520 px while the surrounding Vega pane was capped at
  420 px. Both the count and bp charts now use step-based height
  (`alt.Step(22)` per category) and the pane drops the hard-coded
  height, so the chart grows with the number of matches and the
  x-axis stays visible.

## [0.6.1] - 2026-05-23

### Added
- `pct_ge_5x` column in the Dashboard "Best-covered references"
  table.
- New "Highest mean depth references" Tabulator in the Dashboard,
  re-sorting the same per-reference frame by `mean_depth`
  descending. Surfaces short references with very deep coverage
  that the breadth-based ranking would otherwise hide.

## [0.6.0] - 2026-05-23

### Added
- **Dashboard landing tab** as the first tab of every per-sample
  report. Single-viewport summary: 6-tile KPI strip (raw reads,
  Q30, % host removed, non-host reads, % classified by Kraken
  viral, classified contigs), three side-by-side top-5 cards
  (Kraken species, Kaiju taxa, BLAST matches by cumulative bp),
  per-assembler Assembly summary table and a Best-covered
  references table. Each card carries a one-line pointer to the
  relevant detail tab. Implemented in
  `reporthanter/report/dashboard.py`; exposed as
  `DashboardSection`.
- `BlastProcessor.top_matches_by_bp(df, n=5)` helper used by the
  Dashboard BLAST card.

### Changed
- `ReportGenerator` instantiates `DashboardSection` and prepends
  it to `main_tabs`. The existing six tabs (Read statistics,
  Host alignment, Classification of reads, Assembly statistics,
  Assembly classification, Alignment coverage) keep their layout
  and order.

## [0.5.11] - 2026-05-23

### Changed
- Compact host-alignment bar.

## [0.5.10] - 2026-05-23

### Added
- NCBI Nucleotide link formatter for the `accession` and `chrom`
  columns.

## [0.5.9] - 2026-05-23

### Changed
- Assembly classification split into two charts: contig count and
  cumulative bp shown separately.

## [0.5.8] - 2026-05-22

### Changed
- Coverage references use a matched ordering between the summary
  table and the per-reference tabs (row-click drill-in removed; the
  table row order pins the tab order).

## [0.5.7] - 2026-05-22

### Changed
- Coverage ordering plus row-click drill-in; Host header
  de-duplication; wider Assembly chart.

## [0.5.6] - 2026-05-22

### Changed
- UX polish: chart consolidation, a Coverage summary table, an
  Assembly comparison view and the Host KPI strip.

## [0.5.5] - 2026-05-22

### Added
- Cumulative-bp chart, a per-reference coverage statistics table and
  per-assembler QUAST labels.

## [0.5.4] - 2026-05-22

### Changed
- Six-tab data-flow layout.

## [0.5.3] - 2026-05-22

### Changed
- Dedicated Assembly section for QUAST, separate from Classification
  of Contigs.

## [0.5.2] - 2026-05-22

### Changed
- QUAST sub-tab relocated to Classification of Contigs.

## [0.5.1] - 2026-05-21

### Added
- `sources` column on the coverage labels; per-assembler sub-tab
  layout.

## [0.5.0] - 2026-05-21

### Added
- Multi-assembler contig table: BLAST CSVs are accepted as a list
  (one per assembler) and the contig table carries an `assembler`
  column.

## [0.4.2] - 2026-05-21

### Fixed
- Dropped `interactive()` on the nominal-axis bar charts.

## [0.4.1] - 2026-05-21

### Fixed
- Bars-only charts, fixing blank Kraken / Kaiju / BLAST panels.

## [0.4.0] - 2026-05-21

Breaking release that consolidates onto a single canonical
rendering path.

### Removed (BREAKING)
- The `reporthanter.visualization` package is gone:
  `EnhancedReportGenerator`, `VisualizationConfig`,
  `VisualizationConfigManager`, `LayoutTemplate`, `ColorScheme`,
  `ChartType`, `create_visualization_examples`. Configuration files
  that referenced those names no longer apply.
- `docs/user-guide/VISUAL_IMPROVEMENTS_GUIDE.md` and
  `docs/developer/VISUAL_IMPROVEMENTS_SUMMARY.md`.
- `examples/demos/enhanced_visualization_demo.py` and
  `examples/configurations/config_example.json`.
- The optional `_VISUALIZATION_AVAILABLE` import block in
  `reporthanter/__init__.py`.

### Added
- New `reporthanter.core.palettes` module exporting
  `TAXONOMY_COLORS`, `QUALITY_GRADIENTS`, `SCIENTIFIC_PALETTES`
  (harvested from the retired visualisation layer for use by the
  canonical plot generators).

### Changed
- Bar charts in `KrakenPlotGenerator`, `KaijuPlotGenerator` and
  `BlastPlotGenerator` adopt rounded corners, a thin white stroke,
  nearest-point hover highlighting and (Kraken/Kaiju only)
  inline percentage labels on hits above 2 % — a uniform scientific
  look across the report's three classification panes.
- `FlagstatPlotGenerator` swaps the hard-coded `dark2` scheme for
  the head and tail of the `QUALITY_GRADIENTS["good_to_bad"]`
  palette (unaligned = green, aligned = red).

### Migration
- Code that imported `EnhancedReportGenerator` or
  `VisualizationConfig` must switch to `ReportGenerator` and the
  individual processors. The CLI surface is unchanged from 0.3.1.

## [0.3.1] - 2026-05-21

Patch release rolling up two weeks of stability fixes against real
MiSeq batches and the multi-virus smoke fixture.

### Added
- `CoverageProcessor` + `CoveragePlotGenerator` rendering an
  interactive Altair trace per reference from a mosdepth
  `regions.bed.gz`.
- `QuastProcessor` surfaced as an Alignment Stats sub-tab when
  `--quast_report` is supplied.
- `GenomadProcessor` surfaced as a Classification of Contigs sub-tab
  when `--genomad_summary` is supplied.
- `--virus_names` CLI flag enriching Alignment Coverage tab labels
  with the friendly species name alongside the accession.
- `--mosdepth_regions` required CLI flag (replaces the retired
  `--coverage_folder`).

### Changed
- `--coverage_folder` removed; the bam2plot SVG fallback in
  `CoverageSection` is gone. Coverage is sourced from
  `--mosdepth_regions` only.
- `KrakenProcessor` and `KaijuProcessor` migrated to the Altair 5+
  selection API (`selection_point` + `add_params`). Altair pin
  bumped to `>=6,<7`.
- Section header background darkened to `#067a48` (white text now
  clears WCAG AA contrast).
- Section header height auto-sizes to content (previously clipped
  the second line on Alignment Stats and Raw Classification).
- Contig table copy/download UX (Tabulator clipboard config + CSV
  download button) replaces the CTRL-C instruction.
- Inline data row cap raised from Altair's default 5 000 to 100 000
  so high-resolution coverage traces are not silently truncated.
- Sample headers strip a trailing `_R` from display names.

### Fixed
- Kraken processor's `domain` propagation now accepts `R1` as an
  anchor so the small viral-only Kraken2 DBs (`k2_viral_*`)
  populate the Raw Classification plot correctly.

## [0.3.0] - 2024-XX-XX

### ⚠️ **BREAKING CHANGES**
This is a major version update that removes legacy code for a cleaner, more maintainable codebase.

### Removed
- **BREAKING**: Removed legacy modules (`kraken.py`, `kaiju.py`, `blast.py`, `flagstat.py`, `fastp.py`, `file_utils.py`, `fastx.py`)
- **BREAKING**: Removed legacy `panel_report()` function
- **BREAKING**: Removed individual legacy functions (`wrangle_kraken`, `plot_kraken`, `parse_fastp_json`, etc.)

### Added
- `create_report()` convenience function for easier migration
- Enhanced error messages with specific guidance for migration

### Changed
- **BREAKING**: `reporthanter` package now only exports the new API
- CLI continues to work unchanged (internally uses ReportGenerator)
- All functionality is now available through the modern processor-based architecture

### Migration Path
```python
# Old (0.2.x and earlier):
from reporthanter import panel_report
report = panel_report(blastn_file="...", kraken_file="...", ...)

# New (0.3.x):
from reporthanter import create_report  # Temporary compatibility
report = create_report(blastn_file="...", kraken_file="...", ...)

# Recommended (0.3.x):
from reporthanter import ReportGenerator, DefaultConfig
generator = ReportGenerator(DefaultConfig())
report = generator.generate_report(blastn_file="...", kraken_file="...", ...)
```

### Benefits of 0.3.0
- 🧹 **Cleaner codebase**: 50% reduction in legacy code
- 🚀 **Better performance**: Streamlined architecture
- 🛡️ **More robust**: Comprehensive error handling and validation
- 🔧 **Easier maintenance**: Single source of truth for each functionality
- 📊 **Better testing**: Focused test coverage on modern architecture

## [0.2.0] - 2024-XX-XX

### Added
- **Major Architecture Refactor**: Complete restructuring using MVC pattern
- **Configuration Management**: JSON-based configuration system with sensible defaults
- **Robust Error Handling**: Custom exceptions and comprehensive error recovery
- **Type Safety**: Full type hints throughout the codebase
- **Modular Processors**: Separate, testable processors for each data type
- **Input Validation**: Comprehensive file and argument validation
- **Development Tools**: Pre-commit hooks, linting, formatting, and testing setup
- **CLI Improvements**: Better argument validation, configuration file support, validation-only mode

### Changed
- **Breaking**: Refactored API with new processor classes
- **Breaking**: CLI now requires explicit validation and improved error messages  
- **Improved**: Better separation of concerns between data processing and UI generation
- **Improved**: More consistent and predictable error handling
- **Improved**: Enhanced logging with configurable levels and formats

### Deprecated
- Legacy functions (`wrangle_kraken`, `kraken_df`, `plot_kraken`, etc.) - still available for compatibility

### Technical Improvements
- Abstract base classes for processors and plot generators
- Configuration-driven styling and behavior
- Comprehensive test suite with pytest
- Code formatting with Black and import sorting with isort
- Type checking with mypy
- Documentation generation setup
- Makefile for common development tasks

### Development
- Added `pyproject.toml` for modern Python packaging
- Added `.pre-commit-config.yaml` for automated code quality checks
- Added comprehensive test suite
- Added Makefile for development workflows
- Updated `setup.py` with development dependencies and better metadata

## [0.1.0] - Initial Release

### Added
- Basic HTML report generation for bioinformatics analyses
- Support for Kraken, Kaiju, BLASTN, FastP, and BWA flagstat
- Interactive visualizations using Panel and Altair
- Command-line interface
- Coverage plot integration