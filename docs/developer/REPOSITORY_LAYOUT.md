# Repository layout

Reference for contributors describing where each kind of content
lives in the `reportHanter` repository.

## Top-level

```
reportHanter/
  README.md          Project overview and quickstart
  CLAUDE.md          Guidance for Claude Code sessions
  CHANGELOG.md       Version history
  LICENSE            MIT licence text
  Makefile           Common development tasks
  pyproject.toml     Build, dependency and tooling configuration
  reporthanter/      Source package
  tests/             pytest suite
  docs/              Long-form documentation (this directory)
  examples/          Configuration and demo scripts
  scripts/           Structural and compatibility checks
```

Only `README.md`, `CLAUDE.md`, `CHANGELOG.md` and `LICENSE` should
remain as Markdown at the package root. Any longer document
belongs under `docs/`.

## Source package — `reporthanter/`

```
reporthanter/
  __init__.py                Re-exports the public API surface
  panel_report_cli.py        CLI entry point (`reporthanter`)
  core/                      Configuration, exceptions, abstract
                             bases, interfaces, colour palettes
  processors/                One module per input tool: blast,
                             coverage, fastp, flagstat, genomad,
                             kaiju, kraken, quast
  report/                    `ReportGenerator` and section
                             assembly (alignment, classification
                             of raw reads, classification of
                             contigs, alignment coverage)
```

There is one canonical rendering path: `ReportGenerator`. The
parallel `EnhancedReportGenerator` / `VisualizationConfig` /
`LayoutTemplate` surface that shipped in 0.3.x was retired in
0.4.0; do not re-introduce a second renderer.

The CLI accepts repeated `--blastn_file`, `--quast_report` and
`--genomad_summary` flags so `virusHanter2`'s per-assembler runs
can pass one path per assembler; the singular forms still work
for one-assembler callers.

## Tests — `tests/`

`pytest` discovers from `tests/`. Coverage is configured in
`pyproject.toml` and reports against the `reporthanter` package.
The CLI end-to-end test (`tests/test_cli.py`) drives the CLI
against fixtures under `tests/fixtures/` including a tiny
`mosdepth_regions.bed.gz`.

`scripts/test_0_3_structure.py` is a layout sanity check for the
0.3+ package structure; run it after non-trivial refactors that
move files between subpackages.

## Long-form docs — `docs/`

```
docs/
  README.md                  Index for this directory
  developer/
    REPOSITORY_LAYOUT.md     This document
```

User-facing documentation is intentionally concise — the package
overview, CLI flags, Python API quick-start and the link to the
sibling `virusHanter2` parity notes all live in the top-level
[`README.md`](../../README.md).

## Examples and scripts

- `examples/` ships configuration files and demonstration
  scripts. Each subdirectory carries a short `README.md`.
- `scripts/` holds standalone maintenance scripts (e.g. the 0.3+
  structural sanity check). These are not part of the runtime
  package and are not exercised by `make all-checks`.
