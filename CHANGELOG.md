# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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