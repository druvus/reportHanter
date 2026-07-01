# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working inside
`reportHanter/`. The repository-wide CLAUDE.md at the regionen root
applies as well; this file adds the package-specific detail.

## Scope

`reportHanter` is an installable Python package (CLI plus API) that
renders the per-sample interactive HTML report consumed downstream of
`virusHanter2`. It does no data processing of its own beyond parsing
the tool outputs it is given.

The pairing `virusHanter2 + reportHanter` must reproduce the
parity-locked report and `run_information_<batch>.csv` schema of the
original `virusHanter`. See
[`../virusHanter2/docs/PARITY_NOTES.md`](../virusHanter2/docs/PARITY_NOTES.md).

## Layout

```
reporthanter/
  core/         Configuration, exceptions, abstract bases, interfaces,
                colour palettes (palettes.py)
  processors/   One module per input tool (blast, coverage, fastp,
                flagstat, genomad, kaiju, kraken, quast)
  report/       ReportGenerator and section assembly
  panel_report_cli.py   CLI entry point (panel_report_cli:main)
docs/           Long-form documentation (see docs/README.md)
examples/       Configuration examples
scripts/        Structural and compatibility checks
tests/          pytest suite
```

There is one canonical rendering path: `ReportGenerator`. The
parallel `EnhancedReportGenerator` / `VisualizationConfig` /
`LayoutTemplate` surface that shipped in 0.3.x was retired in 0.4.0;
do not re-introduce a second renderer.

## Entry points

```bash
cd reportHanter
pip install -e ".[dev]"

make all-checks         # ruff format-check, ruff lint, mypy, pytest
make test               # pytest only
make format             # ruff fix + format
```

A `.pre-commit-config.yaml` is provided that mirrors `make all-checks`
(ruff format + lint, mypy) and runs automatically on `git commit` after
`pre-commit install` (called by `make install-dev`).  The hooks are
pinned to the same tool versions used in development.

The CLI is `reporthanter` (defined in `pyproject.toml` as
`panel_report_cli:main`). Its flag set is part of the public
contract with `virusHanter2`'s `generate_report` rule and must
remain stable:

```
--blastn_file (repeatable) \
--kraken_file --kaiju_table --fastp_json --flagstat_file \
--mosdepth_regions --output \
[--quast_report (repeatable) --genomad_summary (repeatable) \
 --virus_names --provenance_file --sample_name \
 --secondary_flagstat_file --secondary_host \
 --config_file --log_level --validate_only]
```

`--blastn_file`, `--quast_report` and `--genomad_summary` use
`action="append"` so virusHanter2's per-assembler runs can pass
one path per assembler. The singular form
(`--blastn_file foo.csv` once) still works.

`--coverage_folder` was removed when `virusHanter2` retired the
`bam2plot` rule; do not re-introduce it.

## Public API surface

Two surfaces are exported from `reporthanter` and must keep
working:

1. `create_report(...)` — high-level wrapper. Required:
   `kraken_file`, `kaiju_table`, `fastp_json`, `flagstat_file`,
   `mosdepth_regions`, plus at least one BLAST CSV via either
   `blastn_files=[...]` (plural, multi-assembler) or
   `blastn_file=...` (singular, legacy). Optional plural / singular
   pairs for `quast_reports` / `quast_report` and
   `genomad_summaries` / `genomad_summary`.
2. `ReportGenerator(config)` plus the individual processors
   (`KrakenProcessor`, `KaijuProcessor`, `BlastProcessor`,
   `FastpProcessor`, `FlagstatProcessor`, `CoverageProcessor`,
   `QuastProcessor`, `GenomadProcessor`) and matching plot
   generators.
3. `DashboardSection` (since 0.6.0) — the landing tab class
   built from the union of processor inputs. Composed by
   `ReportGenerator` as the first tab of the rendered HTML.

Do not re-introduce the legacy free functions removed in 0.3.0
(`panel_report`, `wrangle_kraken`, `plot_kraken`, etc.) or the
0.3.x `EnhancedReportGenerator` / `VisualizationConfig` /
`LayoutTemplate` / `ColorScheme` / `ChartType` /
`VisualizationConfigManager` / `create_visualization_examples`
surface (retired in 0.4.0).

## Conventions

- Python 3.12+, type-hinted, `ruff` clean (format + lint). Line
  length 100. Format with `ruff format`. `mypy` (strict-ish, configured
  in `pyproject.toml`) is enforced as part of `make all-checks`.
- Modest, plain scientific British English in documentation,
  docstrings and comments. No marketing tone, no emoji.
- Charting via Altair 6 (Vega-Lite). Selections use the v5+ API:
  `alt.selection_point` / `alt.selection_interval`, applied with
  `chart.add_params(...)`. The legacy `selection_single`,
  `selection_multi` and `add_selection` names still work via shims
  but emit deprecation noise; do not introduce new uses.
- Report and plotting code lives here, not in
  `virusHanter2/scripts/`.
- Species naming follows whatever the upstream data files
  provide. The pipeline canonicalises to ICTV-binomial species
  names (e.g. `Lymphocryptovirus humangamma4`); the report
  surfaces these verbatim alongside an optional `aliases`
  column rendered as "Also known as" (legacy NCBI scientific
  name + acronyms / common names from `names.dmp`). Do not
  re-introduce name parsing or taxonomy walks in reporthanter —
  the report consumes pre-canonicalised columns.
- Hide raw classifier output from the rendered HTML. Drop
  `*_raw` columns and the BLAST `matches` column at the report
  boundary (processors / Tabulator views / Vega chart data)
  even though they stay on disk for audit. A reviewer should
  see the canonical name, not two names for the same species.
- Documentation belongs under `docs/`; `README.md` and `CLAUDE.md`
  are the only Markdown files that should remain at the package
  root. Link to `docs/` for anything longer.
- Examples that ship with the package go under `examples/`, with a
  short index `README.md` per subdirectory.

## Testing

`pytest` discovers from `tests/`. Coverage is configured in
`pyproject.toml` and reports against the `reporthanter` package.
`scripts/test_0_3_structure.py` is a layout sanity check for the
0.3 package structure; run it after non-trivial refactors that
move files between subpackages.

The CLI end-to-end test (`tests/test_cli.py`) drives
`python -m reporthanter.panel_report_cli` against the fixtures in
`tests/fixtures/` including a tiny `mosdepth_regions.bed.gz`.
