# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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